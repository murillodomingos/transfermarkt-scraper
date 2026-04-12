from datetime import date

import pytest

from tfscrap.utils import normalize_href, parse_tm_date, parse_market_value


class TestParseMarketValue:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("€12.50m", 12_500_000),
            ("€1m", 1_000_000),
            ("€800k", 800_000),
            ("€50k", 50_000),
            ("€120.00m", 120_000_000),
            ("€1.31bn", 1_310_000_000),
            ("€2bn", 2_000_000_000),
            ("$12.50m", 12_500_000),  # outros símbolos devem funcionar
            ("12.50m", 12_500_000),
            ("€12,50m", 12_500_000),  # vírgula decimal estilo europeu
        ],
    )
    def test_parses_valid_values(self, raw, expected):
        assert parse_market_value(raw) == expected

    @pytest.mark.parametrize("raw", ["-", "", None, "N/A", "?"])
    def test_returns_none_for_missing(self, raw):
        assert parse_market_value(raw) is None


class TestParseTmDate:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("May 15, 2003", date(2003, 5, 15)),
            ("Jan 1, 2000", date(2000, 1, 1)),
            ("Dec 31, 1999", date(1999, 12, 31)),
            ("2003-05-15", date(2003, 5, 15)),
            ("15/05/2003", date(2003, 5, 15)),
        ],
    )
    def test_parses_valid_dates(self, raw, expected):
        assert parse_tm_date(raw) == expected

    @pytest.mark.parametrize("raw", ["-", "", None, "unknown"])
    def test_returns_none_for_missing(self, raw):
        assert parse_tm_date(raw) is None


class TestNormalizeHref:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("https://www.transfermarkt.com/foo/bar", "/foo/bar"),
            ("https://www.transfermarkt.com/foo/bar?x=1", "/foo/bar"),
            ("http://transfermarkt.com/foo/bar", "/foo/bar"),
            ("/foo/bar", "/foo/bar"),
            ("/foo/bar?x=1", "/foo/bar"),
            ("/foo/bar#anchor", "/foo/bar"),
            ("  /foo/bar  ", "/foo/bar"),
        ],
    )
    def test_normalizes(self, raw, expected):
        assert normalize_href(raw) == expected

    def test_returns_none_for_empty(self):
        assert normalize_href("") is None
        assert normalize_href(None) is None
