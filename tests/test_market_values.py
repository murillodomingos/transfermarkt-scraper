from datetime import date
from pathlib import Path

from scrapy.http import Request, TextResponse

from tfscrap.spiders.market_values import MarketValuesSpider

FIXTURES = Path(__file__).parent / "fixtures"


def _json_response(parent: dict) -> TextResponse:
    body = (FIXTURES / "market_values_haaland.json").read_bytes()
    url = "https://www.transfermarkt.com/ceapi/marketValueDevelopment/graph/418560"
    req = Request(url=url, meta={"parent": parent})
    return TextResponse(url=url, body=body, encoding="utf-8", request=req)


def test_parses_market_value_history():
    parent = {"type": "player", "href": "/erling-haaland/profil/spieler/418560"}
    items = list(MarketValuesSpider().parse(_json_response(parent)))
    assert len(items) >= 10

    first = items[0]
    assert first["type"] == "market_value"
    assert first["player_href"] == "/erling-haaland/profil/spieler/418560"
    assert first["date"] == date(2016, 12, 18)
    assert first["market_value"] == 200_000
    assert first["club_name"] == "Bryne FK"


def test_api_url_construction_from_player_parent():
    spider = MarketValuesSpider()
    parent = {"type": "player", "href": "/erling-haaland/profil/spieler/418560"}
    url = spider.api_url_for(parent)
    assert url == "https://www.transfermarkt.com/ceapi/marketValueDevelopment/graph/418560"


def test_returns_empty_for_invalid_parent():
    spider = MarketValuesSpider()
    assert spider.api_url_for({}) is None
    assert spider.api_url_for({"href": "/fc-barcelona/startseite/verein/131"}) is None
