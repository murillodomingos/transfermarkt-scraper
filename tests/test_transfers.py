from datetime import date
from pathlib import Path

from scrapy.http import Request, TextResponse

from tfscrap.spiders.transfers import TransfersSpider

FIXTURES = Path(__file__).parent / "fixtures"


def _json_response(parent: dict) -> TextResponse:
    body = (FIXTURES / "transfers_haaland.json").read_bytes()
    url = "https://www.transfermarkt.com/ceapi/transferHistory/list/418560"
    req = Request(url=url, meta={"parent": parent})
    return TextResponse(url=url, body=body, encoding="utf-8", request=req)


def test_parses_json_transfer_history():
    parent = {"type": "player", "href": "/erling-haaland/profil/spieler/418560"}
    items = list(TransfersSpider().parse(_json_response(parent)))
    assert len(items) == 5

    # first transfer: Dortmund -> Man City, 2022-07-01, fee €60m
    t = items[0]
    assert t["type"] == "transfer"
    assert t["player_href"] == "/erling-haaland/profil/spieler/418560"
    assert t["date"] == date(2022, 7, 1)
    assert t["season"] == "22/23"
    assert t["from_club"] == "Dortmund"
    assert t["to_club"] == "Man City"
    assert t["market_value"] == 150_000_000
    assert t["fee"] == 60_000_000


def test_api_url_construction_from_player_parent(monkeypatch):
    """Spider must turn a player parent (/profil/spieler/418560) into the ceapi URL."""
    spider = TransfersSpider()
    parent = {"type": "player", "href": "/erling-haaland/profil/spieler/418560"}
    url = spider.api_url_for(parent)
    assert url == "https://www.transfermarkt.com/ceapi/transferHistory/list/418560"
