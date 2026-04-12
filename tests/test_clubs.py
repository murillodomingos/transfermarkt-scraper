from tfscrap.spiders.clubs import ClubsSpider


def test_parses_all_clubs_from_competition_page(fixture_response):
    url = "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1"
    parent = {"type": "competition", "href": "/premier-league/startseite/wettbewerb/GB1"}
    response = fixture_response("competition_premier_league.html", url, parent)

    items = list(ClubsSpider().parse(response))

    assert len(items) == 20  # Premier League
    for item in items:
        assert item["type"] == "club"
        assert item["name"]
        assert item["href"].startswith("/")
        assert item["competition_href"] == "/premier-league/startseite/wettbewerb/GB1"


def test_first_club_is_manchester_city(fixture_response):
    url = "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1"
    parent = {"type": "competition", "href": "/premier-league/startseite/wettbewerb/GB1"}
    response = fixture_response("competition_premier_league.html", url, parent)

    first = next(iter(ClubsSpider().parse(response)))
    assert first["name"] == "Manchester City"
    assert "/manchester-city/" in first["href"]
    assert first["squad_size"] == 27
    assert first["avg_age"] == 26.0
    assert first["total_market_value"] == 1_310_000_000  # €1.31bn
