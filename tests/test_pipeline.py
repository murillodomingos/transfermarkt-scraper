from __future__ import annotations

import json
from pathlib import Path

import pytest

from tfscrap.pipeline import filter_clubs_by_href, filter_seed_by_league


SEED_LINES = [
    {"type": "competition", "href": "/premier-league/startseite/wettbewerb/GB1"},
    {"type": "competition", "href": "/laliga/startseite/wettbewerb/ES1"},
    {"type": "competition", "href": "/campeonato-brasileiro-serie-a/startseite/wettbewerb/BRA1"},
]

CLUBS_LINES = [
    {"type": "club", "href": "/real-madrid/startseite/verein/418", "name": "Real Madrid", "competition_href": "/laliga/startseite/wettbewerb/ES1"},
    {"type": "club", "href": "/fc-barcelona/startseite/verein/131", "name": "FC Barcelona", "competition_href": "/laliga/startseite/wettbewerb/ES1"},
]


def _write_jsonl(path: Path, items: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


class TestFilterSeedByLeague:
    def test_keeps_matching_league(self, tmp_path):
        seed = tmp_path / "seed.jsonl"
        out  = tmp_path / "out.jsonl"
        _write_jsonl(seed, SEED_LINES)
        filter_seed_by_league(seed, "GB1", out)
        result = _read_jsonl(out)
        assert len(result) == 1
        assert result[0]["href"].endswith("/GB1")

    def test_keeps_all_matching(self, tmp_path):
        seed = tmp_path / "seed.jsonl"
        out  = tmp_path / "out.jsonl"
        _write_jsonl(seed, SEED_LINES)
        filter_seed_by_league(seed, "ES1", out)
        result = _read_jsonl(out)
        assert len(result) == 1
        assert result[0]["href"].endswith("/ES1")

    def test_raises_on_unknown_league(self, tmp_path):
        seed = tmp_path / "seed.jsonl"
        out  = tmp_path / "out.jsonl"
        _write_jsonl(seed, SEED_LINES)
        with pytest.raises(SystemExit, match="XYZ"):
            filter_seed_by_league(seed, "XYZ", out)


class TestFilterClubsByHref:
    def test_keeps_matching_club(self, tmp_path):
        clubs = tmp_path / "clubs.jsonl"
        out   = tmp_path / "out.jsonl"
        _write_jsonl(clubs, CLUBS_LINES)
        filter_clubs_by_href(clubs, "/real-madrid/startseite/verein/418", out)
        result = _read_jsonl(out)
        assert len(result) == 1
        assert result[0]["name"] == "Real Madrid"

    def test_raises_on_unknown_club(self, tmp_path):
        clubs = tmp_path / "clubs.jsonl"
        out   = tmp_path / "out.jsonl"
        _write_jsonl(clubs, CLUBS_LINES)
        with pytest.raises(SystemExit, match="nao-existe"):
            filter_clubs_by_href(clubs, "/nao-existe/verein/999", out)
