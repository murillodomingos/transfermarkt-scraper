from tfscrap.spiders.appearances import AppearancesSpider


def test_parses_appearances_per_competition(fixture_response):
    url = "https://www.transfermarkt.com/erling-haaland/leistungsdaten/spieler/418560"
    parent = {"type": "player", "href": "/erling-haaland/profil/spieler/418560"}
    response = fixture_response("appearances_haaland.html", url, parent)

    items = list(AppearancesSpider().parse(response))
    assert len(items) == 4  # PL, UCL, EFL Cup, FA Cup

    pl = next(i for i in items if i["competition"] == "Premier League")
    assert pl["type"] == "appearance"
    assert pl["player_href"] == "/erling-haaland/profil/spieler/418560"
    assert pl["season"] == "2025"
    assert pl["appearances"] == 30
    assert pl["goals"] == 22
    assert pl["assists"] == 7
    assert pl["minutes"] == 2509
    assert pl["yellow_cards"] == 1
    assert pl["red_cards"] is None  # "-"


def test_dash_becomes_zero_or_none(fixture_response):
    url = "https://www.transfermarkt.com/erling-haaland/leistungsdaten/spieler/418560"
    parent = {"href": "/erling-haaland/profil/spieler/418560"}
    response = fixture_response("appearances_haaland.html", url, parent)

    items = list(AppearancesSpider().parse(response))
    efl = next(i for i in items if i["competition"] == "EFL Cup")
    # "-" columns should be None, not 0 - they mean "no data"
    assert efl["goals"] is None
    assert efl["assists"] is None
    assert efl["appearances"] == 3
    assert efl["minutes"] == 199
