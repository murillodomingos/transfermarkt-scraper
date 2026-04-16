"""Orquestrador do pipeline completo: scraping + carga em DuckDB.

Uso:
    python -m tfscrap.pipeline                                        # todas as ligas
    python -m tfscrap.pipeline --league ES1                           # uma liga
    python -m tfscrap.pipeline --league ES1 --club /real-madrid/startseite/verein/418
    python -m tfscrap.pipeline --skip-load                            # só scraping
    python -m tfscrap.pipeline --skip-scrape                         # só carga
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from tfscrap.load import load

SEEDS_FILE = Path(__file__).parent.parent / "seeds" / "competitions.json"

SPIDER_SEQUENCE = [
    ("competitions", "competitions.jsonl", "competitions.jsonl"),
    ("clubs",        "competitions.jsonl", "clubs.jsonl"),
    ("players",      "clubs.jsonl",        "players.jsonl"),
    ("appearances",  "players.jsonl",      "appearances.jsonl"),
    ("injuries",     "players.jsonl",      "injuries.jsonl"),
    ("transfers",    "players.jsonl",      "transfers.jsonl"),
    ("market_values","players.jsonl",      "market_values.jsonl"),
]


def _run_spider(name: str, parents_file: Path, out_file: Path) -> None:
    import subprocess
    print(f"  → {name} ...", flush=True)
    with out_file.open("w", encoding="utf-8") as fout:
        result = subprocess.run(
            [sys.executable, "-m", "tfscrap", name, "-p", str(parents_file)],
            stdout=fout,
            check=False,
        )
    if result.returncode != 0:
        raise SystemExit(f"Spider '{name}' falhou (exit {result.returncode}). Abortando.")
    lines = sum(1 for _ in out_file.open(encoding="utf-8") if _.strip())
    print(f"     {lines} itens em {out_file.name}", flush=True)


def filter_seed_by_league(seed_path: Path, league_code: str, out_path: Path) -> None:
    pattern = re.compile(rf"/wettbewerb/{re.escape(league_code)}$")
    kept = []
    with seed_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if pattern.search(item.get("href", "")):
                kept.append(line)
    if not kept:
        raise SystemExit(
            f"Liga '{league_code}' não encontrada em {seed_path}. "
            f"Opções: {_available_leagues(seed_path)}"
        )
    out_path.write_text("\n".join(kept) + "\n", encoding="utf-8")


def filter_clubs_by_href(clubs_path: Path, club_href: str, out_path: Path) -> None:
    kept = []
    with clubs_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if item.get("href") == club_href:
                kept.append(line)
    if not kept:
        raise SystemExit(
            f"Clube '{club_href}' não encontrado em {clubs_path}. "
            "Verifique o href e a liga passados."
        )
    out_path.write_text("\n".join(kept) + "\n", encoding="utf-8")


def _available_leagues(seed_path: Path) -> str:
    codes = []
    with seed_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            href = json.loads(line).get("href", "")
            m = re.search(r"/wettbewerb/(\w+)$", href)
            if m:
                codes.append(m.group(1))
    return ", ".join(codes)


def run_pipeline(
    league: str | None,
    club: str | None,
    data_dir: Path,
    db_path: Path,
    skip_scrape: bool,
    skip_load: bool,
) -> None:
    if club and not league:
        raise SystemExit("--club requer --league. Ex: --league ES1 --club /real-madrid/.../418")

    data_dir.mkdir(parents=True, exist_ok=True)

    if not skip_scrape:
        # determina seed de entrada
        if league:
            seed_path = data_dir / "_seed.jsonl"
            filter_seed_by_league(SEEDS_FILE, league, seed_path)
            print(f"Liga: {league}")
        else:
            seed_path = SEEDS_FILE
            print("Ligas: todas do seed")

        for spider, in_name, out_name in SPIDER_SEQUENCE:
            in_path  = seed_path if spider == "competitions" else data_dir / in_name
            out_path = data_dir / out_name
            _run_spider(spider, in_path, out_path)

            if spider == "clubs" and club:
                filtered = data_dir / "_clubs_filtered.jsonl"
                filter_clubs_by_href(data_dir / out_name, club, filtered)
                # substitui clubs.jsonl pelo filtrado
                filtered.replace(data_dir / "clubs.jsonl")
                print(f"  (filtrado para clube: {club})")

    if not skip_load:
        print(f"\nCarregando em {db_path} ...")
        counts = load(data_dir, db_path)
        print(f"Pronto:")
        for table, n in counts.items():
            print(f"  {table:<22} {n:>8,}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tfscrap.pipeline",
        description="Pipeline completo: scraping → DuckDB.",
    )
    parser.add_argument("--league", default=None, metavar="CODE",
                        help="código da liga (ex: GB1, ES1, BRA1)")
    parser.add_argument("--club", default=None, metavar="HREF",
                        help="href do clube (ex: /real-madrid/startseite/verein/418)")
    parser.add_argument("--data-dir", default=Path("data"), type=Path)
    parser.add_argument("--db", default=Path("db/tfscrap.duckdb"), type=Path)
    parser.add_argument("--skip-load", action="store_true",
                        help="só scraping, sem carregar no DuckDB")
    parser.add_argument("--skip-scrape", action="store_true",
                        help="só carga no DuckDB (reusa JSONL existentes)")
    args = parser.parse_args(argv)

    run_pipeline(
        league=args.league,
        club=args.club,
        data_dir=args.data_dir,
        db_path=args.db,
        skip_scrape=args.skip_scrape,
        skip_load=args.skip_load,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
