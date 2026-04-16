-- Entrega 04 — star schema carregado a partir dos JSONL produzidos pelos spiders.
-- Política: drop-and-reload a cada execução do loader.

DROP TABLE IF EXISTS fact_market_value;
DROP TABLE IF EXISTS fact_transfer;
DROP TABLE IF EXISTS fact_injury;
DROP TABLE IF EXISTS fact_stats;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_player;
DROP TABLE IF EXISTS dim_club;
DROP TABLE IF EXISTS dim_competition;

CREATE TABLE dim_competition (
    competition_id   INTEGER PRIMARY KEY,
    href             VARCHAR UNIQUE,        -- NULL para stubs (competições fora do seed)
    competition_name VARCHAR,
    country          VARCHAR,
    season           VARCHAR
);

CREATE TABLE dim_club (
    club_id             INTEGER PRIMARY KEY,
    href                VARCHAR UNIQUE,        -- NULL para clubes stub (fora do seed)
    club_name           VARCHAR NOT NULL,
    competition_id      INTEGER REFERENCES dim_competition(competition_id),
    squad_size          INTEGER,
    avg_age             DOUBLE,
    total_market_value  BIGINT
);

CREATE TABLE dim_player (
    player_id             INTEGER PRIMARY KEY,
    href                  VARCHAR UNIQUE NOT NULL,
    name                  VARCHAR,
    date_birth            DATE,
    nationality           VARCHAR,
    position              VARCHAR,
    foot                  VARCHAR,
    height_cm             INTEGER,
    joined_date           DATE,
    contract_until        DATE,
    current_market_value  BIGINT
);

CREATE TABLE dim_date (
    date_id  INTEGER PRIMARY KEY,              -- YYYYMMDD
    date     DATE UNIQUE NOT NULL,
    season   VARCHAR,
    year     INTEGER,
    month    INTEGER,
    day      INTEGER
);

CREATE TABLE fact_stats (
    player_id        INTEGER NOT NULL REFERENCES dim_player(player_id),
    club_id          INTEGER NOT NULL REFERENCES dim_club(club_id),
    competition_id   INTEGER NOT NULL REFERENCES dim_competition(competition_id),
    date_id          INTEGER NOT NULL REFERENCES dim_date(date_id),
    appearances      INTEGER,
    goals            INTEGER,
    assists          INTEGER,
    yellow_cards     INTEGER,
    red_cards        INTEGER,
    minutes_played   INTEGER,
    PRIMARY KEY (player_id, club_id, competition_id, date_id)
);

CREATE TABLE fact_injury (
    player_id       INTEGER NOT NULL REFERENCES dim_player(player_id),
    start_date_id   INTEGER NOT NULL REFERENCES dim_date(date_id),
    end_date_id     INTEGER NOT NULL REFERENCES dim_date(date_id),
    injury_type     VARCHAR,
    days_out        INTEGER,
    games_missed    INTEGER,
    PRIMARY KEY (player_id, start_date_id, end_date_id)
);

CREATE TABLE fact_transfer (
    player_id       INTEGER NOT NULL REFERENCES dim_player(player_id),
    from_club_id    INTEGER NOT NULL REFERENCES dim_club(club_id),
    to_club_id      INTEGER NOT NULL REFERENCES dim_club(club_id),
    date_id         INTEGER NOT NULL REFERENCES dim_date(date_id),
    from_club_name  VARCHAR,
    to_club_name    VARCHAR,
    market_value    BIGINT,
    transfer_fee    BIGINT,
    PRIMARY KEY (player_id, from_club_id, to_club_id, date_id)
);

CREATE TABLE fact_market_value (
    player_id    INTEGER NOT NULL REFERENCES dim_player(player_id),
    date_id      INTEGER NOT NULL REFERENCES dim_date(date_id),
    market_value BIGINT,
    PRIMARY KEY (player_id, date_id)
);
