# tfscrap

Cleanroom Transfermarkt scraper — SME0829 / ICMC-USP, 1º sem/2026.
Entrega 02 do projeto *Mineração Estatística e Modelagem Preditiva de Valor de Ativos no Mercado
de Futebol*.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

### Pipeline completo (recomendado)

```bash
# todas as ligas do seed
python -m tfscrap.pipeline

# uma liga inteira (códigos disponíveis: GB1, ES1, IT1, L1, FR1, BRA1)
python -m tfscrap.pipeline --league ES1

# um clube específico dentro de uma liga
python -m tfscrap.pipeline --league ES1 --club /real-madrid/startseite/verein/418

# só scraping (sem carregar no DuckDB)
python -m tfscrap.pipeline --league BRA1 --skip-load

# só carga no DuckDB (reusa JSONL existentes em data/)
python -m tfscrap.pipeline --skip-scrape
```

### Execução manual / debug

Cada spider pode ser rodado individualmente. A saída (JSONL) de um é a entrada do próximo.

```bash
python -m tfscrap competitions -p seeds/competitions.json > data/competitions.jsonl
python -m tfscrap clubs        -p data/competitions.jsonl > data/clubs.jsonl
python -m tfscrap players      -p data/clubs.jsonl        > data/players.jsonl
python -m tfscrap appearances  -p data/players.jsonl      > data/appearances.jsonl
python -m tfscrap injuries     -p data/players.jsonl      > data/injuries.jsonl
python -m tfscrap transfers    -p data/players.jsonl      > data/transfers.jsonl
python -m tfscrap market_values -p data/players.jsonl     > data/market_values.jsonl
```

Todos aceitam `-p <arquivo>` ou leem stdin.

## Entidades emitidas

| spider        | campos principais                                                           |
|---------------|------------------------------------------------------------------------------|
| competitions  | type, name, country, season, href                                            |
| clubs         | type, name, href, competition_href, squad_size, avg_age, total_market_value  |
| players       | type, name, href, club_href, dob, age, nationality, position, foot, height_cm, joined, contract_until, market_value |
| appearances   | type, player_href, competition, season, appearances, goals, assists, minutes, yellow/red cards |
| injuries      | type, player_href, season, injury, from, until, days_out, games_missed       |
| transfers     | type, player_href, date, season, from_club, to_club, market_value, fee       |

As variáveis-alvo do modelo do PDF (idade, lesões, minutos, gols, assistências, valor de mercado,
tempo de contrato) estão cobertas.

## Testes

```bash
pytest -q
```

Todos os parsers são testados contra fixtures HTML/JSON reais do Transfermarkt salvas em
`tests/fixtures/`. Nenhum teste faz rede.

## Ética e limites

- `ROBOTSTXT_OBEY=True`, `DOWNLOAD_DELAY=2`, `AUTOTHROTTLE_ENABLED=True`.
- User-Agent identifica o projeto acadêmico.
- Cache HTTP local (`.scrapy/httpcache`) reduz carga durante desenvolvimento.

## Entrega 04 — Carga em DuckDB (star schema)

Depois de gerar os JSONL em `data/`, rode o loader:

```bash
python -m tfscrap.load --data-dir data --db db/tfscrap.duckdb
```

O script dropa e recria todo o schema (`schema.sql`) e popula 4 dimensões
(`dim_competition`, `dim_club`, `dim_player`, `dim_date`) e 3 fatos
(`fact_stats`, `fact_injury`, `fact_transfer`).

O arquivo `db/tfscrap.duckdb` é versionado no Git para que qualquer colaborador
com o repo clonado consulte os dados localmente — sem servidor:

```bash
duckdb db/tfscrap.duckdb
# ou via Python:
python -c "import duckdb; print(duckdb.connect('db/tfscrap.duckdb').execute('SELECT COUNT(*) FROM dim_player').fetchone())"
```

> **Atenção**: o formato `.duckdb` é versionado — mantenha `duckdb>=1.1,<2` no
> `requirements.txt` para garantir compatibilidade entre colaboradores. Se o
> arquivo passar de ~50 MB, migre para git-lfs.

Para o sub-tree completo (scraping + carga):

```bash
python -m tfscrap.pipeline                # todas as ligas
python -m tfscrap.pipeline --league BRA1  # ou só uma
```

Ou passo a passo (debug):

```bash
python -m tfscrap competitions -p seeds/competitions.json > data/competitions.jsonl
python -m tfscrap clubs         -p data/competitions.jsonl > data/clubs.jsonl
python -m tfscrap players       -p data/clubs.jsonl        > data/players.jsonl
python -m tfscrap appearances   -p data/players.jsonl      > data/appearances.jsonl
python -m tfscrap injuries      -p data/players.jsonl      > data/injuries.jsonl
python -m tfscrap transfers     -p data/players.jsonl      > data/transfers.jsonl
python -m tfscrap market_values -p data/players.jsonl      > data/market_values.jsonl
python -m tfscrap.load          --data-dir data --db db/tfscrap.duckdb
```

## Fora de escopo nesta entrega

- Feature engineering e modelos preditivos — Entrega 06.
