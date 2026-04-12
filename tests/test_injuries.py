from datetime import date

from tfscrap.spiders.injuries import InjuriesSpider


def test_parses_injury_history(fixture_response):
    url = "https://www.transfermarkt.com/erling-haaland/verletzungen/spieler/418560"
    parent = {"type": "player", "href": "/erling-haaland/profil/spieler/418560"}
    response = fixture_response("injuries_haaland.html", url, parent)

    items = list(InjuriesSpider().parse(response))
    assert len(items) >= 10
    first = items[0]
    assert first["type"] == "injury"
    assert first["player_href"] == "/erling-haaland/profil/spieler/418560"
    assert first["season"] == "25/26"
    assert first["injury"] == "Knock"
    assert first["from"] == date(2026, 2, 26)
    assert first["until"] == date(2026, 3, 1)
    assert first["days_out"] == 4
    assert first["games_missed"] == 1
