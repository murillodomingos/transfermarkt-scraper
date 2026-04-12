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

Spiders são pipeáveis: a saída (JSONL) de um spider é a entrada do próximo.

```bash
# 1) enriquece a semente com nome/país/temporada
python -m tfscrap competitions -p seeds/competitions.json > data/competitions.jsonl

# 2) lista clubes em cada competição
python -m tfscrap clubs -p data/competitions.jsonl > data/clubs.jsonl

# 3) dados detalhados de jogadores (visita a página de perfil de cada um)
python -m tfscrap players -p data/clubs.jsonl > data/players.jsonl

# 4) agregados por competição-temporada (desempenho)
python -m tfscrap appearances -p data/players.jsonl > data/appearances.jsonl

# 5) histórico de lesões
python -m tfscrap injuries -p data/players.jsonl > data/injuries.jsonl

# 6) histórico de transferências (via ceapi/transferHistory)
python -m tfscrap transfers -p data/players.jsonl > data/transfers.jsonl
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

## Fora de escopo nesta entrega

- Carga em DuckDB (star schema) — Entrega 04.
- Feature engineering e modelos preditivos — Entrega 06.
