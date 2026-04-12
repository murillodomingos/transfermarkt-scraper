from datetime import date

import scrapy

from tfscrap.spiders.players import PlayersSpider


def test_squad_page_yields_profile_requests(fixture_response):
    """Given a club squad page, the spider emits a Request per unique player profile."""
    url = "https://www.transfermarkt.com/manchester-city/startseite/verein/281"
    parent = {"type": "club", "href": "/manchester-city/startseite/verein/281"}
    response = fixture_response("club_manchester_city.html", url, parent)

    outputs = list(PlayersSpider().parse(response))
    requests = [o for o in outputs if isinstance(o, scrapy.Request)]
    assert len(requests) == 27
    assert all("/profil/spieler/" in r.url for r in requests)
    assert all(r.meta["parent"]["href"] == "/manchester-city/startseite/verein/281" for r in requests)


def test_profile_page_yields_complete_player_item(fixture_response):
    url = "https://www.transfermarkt.com/erling-haaland/profil/spieler/418560"
    parent = {"type": "club", "href": "/manchester-city/startseite/verein/281"}
    response = fixture_response("player_haaland.html", url, parent)

    items = list(PlayersSpider().parse_profile(response))
    assert len(items) == 1
    p = items[0]
    assert p["type"] == "player"
    assert "Haaland" in p["name"]
    assert p["href"] == "/erling-haaland/profil/spieler/418560"
    assert p["club_href"] == "/manchester-city/startseite/verein/281"
    assert p["dob"] == date(2000, 7, 21)
    assert p["age"] == 25
    assert p["nationality"] == "Norway"
    assert p["foot"] == "left"
    assert "Centre-Forward" in p["position"]
    assert p["height_cm"] == 195
    assert p["joined"] == date(2022, 7, 1)
    assert p["contract_until"] == date(2034, 6, 30)
    assert p["market_value"] == 200_000_000
