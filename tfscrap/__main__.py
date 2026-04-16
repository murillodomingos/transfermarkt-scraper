from __future__ import annotations

import argparse
import sys

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from tfscrap.spiders.appearances import AppearancesSpider
from tfscrap.spiders.clubs import ClubsSpider
from tfscrap.spiders.competitions import CompetitionsSpider
from tfscrap.spiders.injuries import InjuriesSpider
from tfscrap.spiders.market_values import MarketValuesSpider
from tfscrap.spiders.players import PlayersSpider
from tfscrap.spiders.transfers import TransfersSpider

SPIDERS = {
    "competitions": CompetitionsSpider,
    "clubs": ClubsSpider,
    "players": PlayersSpider,
    "appearances": AppearancesSpider,
    "injuries": InjuriesSpider,
    "transfers": TransfersSpider,
    "market_values": MarketValuesSpider,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tfscrap",
        description="Transfermarkt scraper (cleanroom) — pipes JSONL between spiders.",
    )
    parser.add_argument("spider", choices=SPIDERS.keys(), help="spider name")
    parser.add_argument(
        "-p", "--parents", default=None, help="path to JSONL with parent items (default: stdin)"
    )
    parser.add_argument("-s", "--season", default=None, help="season id (e.g. 2025)")
    parser.add_argument(
        "--base-url", default="https://www.transfermarkt.com", help="base URL override"
    )
    args = parser.parse_args(argv)

    settings = get_project_settings()
    # Emit items as JSONL on stdout.
    settings.set("FEEDS", {"stdout:": {"format": "jsonlines", "encoding": "utf-8"}})

    process = CrawlerProcess(settings)
    process.crawl(
        SPIDERS[args.spider],
        parents=args.parents,
        season=args.season,
        base_url=args.base_url,
    )
    process.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
