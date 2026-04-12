from tfscrap.spiders.competitions import CompetitionsSpider


def test_parses_competition_metadata(fixture_response):
    url = "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1"
    parent = {"type": "competition", "href": "/premier-league/startseite/wettbewerb/GB1"}
    response = fixture_response("competition_premier_league.html", url, parent)

    items = list(CompetitionsSpider().parse(response))

    assert len(items) == 1
    item = items[0]
    assert item["type"] == "competition"
    assert item["name"] == "Premier League"
    assert item["country"] == "England"
    assert item["season"] == "2025"
    assert item["href"] == "/premier-league/startseite/wettbewerb/GB1"


def test_carries_parent_href_when_page_link_missing(fixture_response):
    url = "https://www.transfermarkt.com/x/startseite/wettbewerb/GB1"
    parent = {"type": "competition", "href": "/original/path"}
    response = fixture_response("competition_premier_league.html", url, parent)
    item = next(iter(CompetitionsSpider().parse(response)))
    # the parent href is preserved (canonical path used downstream)
    assert item["href"] == "/original/path"
