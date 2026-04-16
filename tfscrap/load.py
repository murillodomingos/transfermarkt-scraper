"""Entrega 04 — carga dos JSONL produzidos pelos spiders em um DuckDB star schema.

Uso:
    python -m tfscrap.load --data-dir data --db db/tfscrap.duckdb

Política: drop-and-reload a cada execução (snapshot acadêmico).
"""

from __future__ import annotations

import argparse
import sys
from importlib.resources import files
from pathlib import Path

import duckdb

RAW_SOURCES = [
    "competitions",
    "clubs",
    "players",
    "appearances",
    "injuries",
    "transfers",
    "market_values",
]


def _schema_sql() -> str:
    return (files("tfscrap") / "sql" / "schema.sql").read_text(encoding="utf-8")


def _register_raw_views(con: duckdb.DuckDBPyConnection, data_dir: Path) -> set[str]:
    """Create a TEMP VIEW per JSONL source found. Returns the set of names registered."""
    present: set[str] = set()
    for name in RAW_SOURCES:
        path = data_dir / f"{name}.jsonl"
        if path.exists() and path.stat().st_size > 0:
            # read_json_auto path não aceita parâmetro preparado; interpolamos com escape.
            escaped = str(path).replace("'", "''")
            con.execute(
                f"CREATE TEMP VIEW raw_{name} AS SELECT * FROM read_json_auto('{escaped}')"
            )
            present.add(name)
    return present


def _load_dim_competition(con: duckdb.DuckDBPyConnection, present: set[str]) -> None:
    if "competitions" not in present:
        return
    con.execute("""
        INSERT INTO dim_competition (competition_id, href, competition_name, country, season)
        SELECT
            row_number() OVER (ORDER BY href) AS competition_id,
            href,
            name        AS competition_name,
            country,
            season
        FROM raw_competitions
        WHERE href IS NOT NULL
    """)


def _load_dim_club(con: duckdb.DuckDBPyConnection, present: set[str]) -> None:
    if "clubs" not in present:
        return
    con.execute("""
        INSERT INTO dim_club (club_id, href, club_name, competition_id,
                              squad_size, avg_age, total_market_value)
        SELECT
            row_number() OVER (ORDER BY c.href) AS club_id,
            c.href,
            c.name AS club_name,
            comp.competition_id,
            c.squad_size,
            c.avg_age,
            c.total_market_value
        FROM raw_clubs c
        LEFT JOIN dim_competition comp ON comp.href = c.competition_href
        WHERE c.href IS NOT NULL AND c.name IS NOT NULL
    """)


def _load_dim_player(con: duckdb.DuckDBPyConnection, present: set[str]) -> None:
    if "players" not in present:
        return
    con.execute("""
        INSERT INTO dim_player (
            player_id, href, name, date_birth, nationality, position, foot, height_cm
        )
        SELECT
            row_number() OVER (ORDER BY href) AS player_id,
            href,
            name,
            TRY_CAST(dob AS DATE) AS date_birth,
            nationality,
            position,
            foot,
            height_cm
        FROM raw_players
        WHERE href IS NOT NULL
        QUALIFY row_number() OVER (PARTITION BY href ORDER BY name NULLS LAST) = 1
    """)


def _load_dim_date(con: duckdb.DuckDBPyConnection, present: set[str]) -> None:
    """Consolida toda data referenciada por fatos em dim_date.

    Para appearances (grão sazonal), sintetizamos 1º de julho da temporada.
    """
    parts: list[str] = []
    if "appearances" in present:
        parts.append("""
            SELECT make_date(TRY_CAST(season AS INTEGER), 7, 1) AS date,
                   CAST(season AS VARCHAR)                     AS season
            FROM raw_appearances
            WHERE TRY_CAST(season AS INTEGER) IS NOT NULL
        """)
    if "injuries" in present:
        parts.append("""
            SELECT TRY_CAST("from" AS DATE) AS date, season FROM raw_injuries WHERE "from" IS NOT NULL
            UNION
            SELECT TRY_CAST("until" AS DATE) AS date, season FROM raw_injuries WHERE "until" IS NOT NULL
        """)
    if "transfers" in present:
        parts.append("""
            SELECT TRY_CAST(date AS DATE) AS date, CAST(season AS VARCHAR) AS season
            FROM raw_transfers
            WHERE date IS NOT NULL
        """)
    if "market_values" in present:
        parts.append("""
            SELECT TRY_CAST(date AS DATE) AS date, NULL AS season
            FROM raw_market_values
            WHERE date IS NOT NULL
        """)
    if "players" in present:
        parts.append("""
            SELECT TRY_CAST(joined AS DATE) AS date, NULL AS season
            FROM raw_players WHERE joined IS NOT NULL
            UNION
            SELECT TRY_CAST(contract_until AS DATE) AS date, NULL AS season
            FROM raw_players WHERE contract_until IS NOT NULL
        """)
    if not parts:
        return

    union_sql = " UNION ALL ".join(parts)
    con.execute(f"""
        INSERT INTO dim_date (date_id, date, season, year, month, day)
        SELECT
            CAST(strftime(date, '%Y%m%d') AS INTEGER) AS date_id,
            date,
            any_value(season)                         AS season,
            EXTRACT('year'  FROM date)::INTEGER       AS year,
            EXTRACT('month' FROM date)::INTEGER       AS month,
            EXTRACT('day'   FROM date)::INTEGER       AS day
        FROM ({union_sql}) u
        WHERE date IS NOT NULL
        GROUP BY date
    """)


def _add_stub_competitions_from_appearances(
    con: duckdb.DuckDBPyConnection, present: set[str]
) -> None:
    """O spider de appearances emite `competition` como nome de exibição (string), não href.
    Para competições fora do seed, inserimos stubs em dim_competition para preservar a FK."""
    if "appearances" not in present:
        return
    con.execute("""
        INSERT INTO dim_competition (competition_id, href, competition_name, country, season)
        SELECT
            (SELECT COALESCE(MAX(competition_id), 0) FROM dim_competition)
                + row_number() OVER (ORDER BY competition) AS competition_id,
            NULL AS href,
            competition AS competition_name,
            NULL AS country,
            NULL AS season
        FROM (
            SELECT DISTINCT competition
            FROM raw_appearances
            WHERE competition IS NOT NULL
              AND competition NOT IN (
                  SELECT competition_name FROM dim_competition WHERE competition_name IS NOT NULL
              )
        )
    """)


def _add_stub_clubs_from_transfers(
    con: duckdb.DuckDBPyConnection, present: set[str]
) -> None:
    """O spider de transfers emite `from_club`/`to_club` como nome (não href).
    Clubes fora do seed viram stubs com href=NULL para preservar a FK."""
    if "transfers" not in present:
        return
    con.execute("""
        INSERT INTO dim_club (club_id, href, club_name, competition_id,
                              squad_size, avg_age, total_market_value)
        SELECT
            (SELECT COALESCE(MAX(club_id), 0) FROM dim_club)
                + row_number() OVER (ORDER BY club_name) AS club_id,
            NULL AS href,
            club_name,
            NULL, NULL, NULL, NULL
        FROM (
            SELECT DISTINCT trim(club_name) AS club_name FROM (
                SELECT from_club AS club_name FROM raw_transfers WHERE from_club IS NOT NULL
                UNION
                SELECT to_club   AS club_name FROM raw_transfers WHERE to_club   IS NOT NULL
            )
            WHERE club_name NOT IN (SELECT club_name FROM dim_club)
        )
    """)


def _load_fact_stats(con: duckdb.DuckDBPyConnection, present: set[str]) -> None:
    if "appearances" not in present or "players" not in present:
        return
    con.execute("""
        INSERT INTO fact_stats (player_id, club_id, competition_id, date_id,
                                appearances, goals, assists, yellow_cards, red_cards,
                                minutes_played)
        SELECT
            p.player_id,
            cl.club_id,
            comp.competition_id,
            CAST(strftime(make_date(TRY_CAST(a.season AS INTEGER), 7, 1), '%Y%m%d') AS INTEGER)
                AS date_id,
            max(a.appearances)  AS appearances,
            max(a.goals)        AS goals,
            max(a.assists)      AS assists,
            max(a.yellow_cards) AS yellow_cards,
            max(a.red_cards)    AS red_cards,
            max(a.minutes)      AS minutes_played
        FROM raw_appearances a
        JOIN dim_player       p    ON p.href = a.player_href
        JOIN raw_players      rp   ON rp.href = a.player_href
        JOIN dim_club         cl   ON cl.href = rp.club_href
        JOIN dim_competition  comp ON comp.competition_name = a.competition
        WHERE TRY_CAST(a.season AS INTEGER) IS NOT NULL
        GROUP BY p.player_id, cl.club_id, comp.competition_id,
                 CAST(strftime(make_date(TRY_CAST(a.season AS INTEGER), 7, 1), '%Y%m%d') AS INTEGER)
    """)


def _load_fact_injury(con: duckdb.DuckDBPyConnection, present: set[str]) -> None:
    if "injuries" not in present:
        return
    con.execute("""
        INSERT INTO fact_injury (player_id, start_date_id, end_date_id,
                                 injury_type, days_out, games_missed)
        SELECT
            p.player_id,
            CAST(strftime(TRY_CAST(i."from"  AS DATE), '%Y%m%d') AS INTEGER) AS start_date_id,
            CAST(strftime(TRY_CAST(i."until" AS DATE), '%Y%m%d') AS INTEGER) AS end_date_id,
            any_value(i.injury)      AS injury_type,
            max(i.days_out)          AS days_out,
            max(i.games_missed)      AS games_missed
        FROM raw_injuries i
        JOIN dim_player p ON p.href = i.player_href
        WHERE i."from"  IS NOT NULL
          AND i."until" IS NOT NULL
        GROUP BY p.player_id,
                 CAST(strftime(TRY_CAST(i."from"  AS DATE), '%Y%m%d') AS INTEGER),
                 CAST(strftime(TRY_CAST(i."until" AS DATE), '%Y%m%d') AS INTEGER)
    """)


def _load_fact_market_value(con: duckdb.DuckDBPyConnection, present: set[str]) -> None:
    if "market_values" not in present:
        return
    con.execute("""
        INSERT INTO fact_market_value (player_id, date_id, market_value)
        SELECT
            p.player_id,
            CAST(strftime(TRY_CAST(mv.date AS DATE), '%Y%m%d') AS INTEGER) AS date_id,
            max(mv.market_value) AS market_value
        FROM raw_market_values mv
        JOIN dim_player p ON p.href = mv.player_href
        WHERE mv.date IS NOT NULL
        GROUP BY p.player_id,
                 CAST(strftime(TRY_CAST(mv.date AS DATE), '%Y%m%d') AS INTEGER)
    """)


def _load_fact_transfer(con: duckdb.DuckDBPyConnection, present: set[str]) -> None:
    if "transfers" not in present:
        return
    con.execute("""
        INSERT INTO fact_transfer (player_id, from_club_id, to_club_id, date_id,
                                   from_club_name, to_club_name, market_value, transfer_fee)
        SELECT
            p.player_id,
            fc.club_id  AS from_club_id,
            tc.club_id  AS to_club_id,
            CAST(strftime(TRY_CAST(t.date AS DATE), '%Y%m%d') AS INTEGER) AS date_id,
            t.from_club AS from_club_name,
            t.to_club   AS to_club_name,
            max(t.market_value) AS market_value,
            max(t.fee)          AS transfer_fee
        FROM raw_transfers t
        JOIN dim_player p ON p.href = t.player_href
        JOIN dim_club fc  ON fc.club_name = t.from_club
        JOIN dim_club tc  ON tc.club_name = t.to_club
        WHERE t.date IS NOT NULL
        GROUP BY p.player_id, fc.club_id, tc.club_id,
                 CAST(strftime(TRY_CAST(t.date AS DATE), '%Y%m%d') AS INTEGER),
                 t.from_club, t.to_club
    """)


def _load_fact_contract(con: duckdb.DuckDBPyConnection, present: set[str]) -> None:
    if "players" not in present:
        return
    con.execute("""
        INSERT INTO fact_contract (player_id, club_id, joined_date_id, contract_until_id)
        SELECT
            p.player_id,
            cl.club_id,
            CAST(strftime(TRY_CAST(rp.joined         AS DATE), '%Y%m%d') AS INTEGER),
            CAST(strftime(TRY_CAST(rp.contract_until AS DATE), '%Y%m%d') AS INTEGER)
        FROM raw_players rp
        JOIN dim_player p  ON p.href  = rp.href
        JOIN dim_club   cl ON cl.href = rp.club_href
        WHERE rp.joined IS NOT NULL AND rp.contract_until IS NOT NULL
        QUALIFY row_number() OVER (
            PARTITION BY p.player_id, cl.club_id ORDER BY rp.joined DESC
        ) = 1
    """)


def load(data_dir: Path, db_path: Path) -> dict[str, int]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    con = duckdb.connect(str(db_path))
    try:
        con.execute(_schema_sql())
        present = _register_raw_views(con, data_dir)
        if not present:
            raise SystemExit(f"no JSONL sources found in {data_dir}/ — run the spiders first")

        _load_dim_competition(con, present)
        _load_dim_club(con, present)
        _load_dim_player(con, present)
        _add_stub_competitions_from_appearances(con, present)
        _add_stub_clubs_from_transfers(con, present)
        _load_dim_date(con, present)
        _load_fact_stats(con, present)
        _load_fact_injury(con, present)
        _load_fact_transfer(con, present)
        _load_fact_market_value(con, present)
        _load_fact_contract(con, present)

        counts = {}
        for table in [
            "dim_competition", "dim_club", "dim_player", "dim_date",
            "fact_stats", "fact_injury", "fact_transfer", "fact_market_value", "fact_contract",
        ]:
            counts[table] = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return counts
    finally:
        con.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tfscrap.load",
        description="Load scraped JSONL into a DuckDB star schema (Entrega 04).",
    )
    parser.add_argument("--data-dir", default="data", type=Path)
    parser.add_argument("--db", default=Path("db/tfscrap.duckdb"), type=Path)
    args = parser.parse_args(argv)

    counts = load(args.data_dir, args.db)
    print(f"loaded into {args.db}:")
    for table, n in counts.items():
        print(f"  {table:<18} {n:>8,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
