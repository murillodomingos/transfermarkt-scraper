from __future__ import annotations

import re
from collections.abc import Iterator

import scrapy

from tfscrap.spiders.base import DEFAULT_HEADERS, BaseSpider
from tfscrap.utils import normalize_href

_PROFIL_RE = re.compile(r"/profil/spieler/(\d+)")


def _int(raw: str | None) -> int | None:
    if raw is None:
        return None
    s = raw.strip().replace("'", "").replace(".", "").replace(",", "")
    if not s or s == "-":
        return None
    try:
        return int(s)
    except ValueError:
        return None


class AppearancesSpider(BaseSpider):
    """One item per (player, competition, season) with aggregate stats."""

    name = "appearances"

    def _leistungsdaten_url(self, href: str, season: str | None = None) -> str:
        url = re.sub(r"/profil/spieler/", "/leistungsdaten/spieler/", self.base_url + href)
        if season:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}saison={season}"
        return url

    def start_requests(self) -> Iterator[scrapy.Request]:
        for parent in self.read_parents():
            href = parent.get("href") or ""
            yield scrapy.Request(
                url=self._leistungsdaten_url(href),
                headers=DEFAULT_HEADERS,
                meta={"parent": parent, "fanout": True},
                callback=self.parse,
            )

    def parse(self, response, **kwargs):
        parent = response.meta.get("parent") or {}
        player_href = normalize_href(parent.get("href")) or normalize_href(response.url)
        current_season = response.css("select[name=saison] option[selected]::attr(value)").get()
        season = response.meta.get("season") or current_season

        if response.meta.get("fanout"):
            seasons = response.css("select[name=saison] option::attr(value)").getall()
            seasons = [s for s in seasons if s and s != current_season]
            href = parent.get("href") or ""
            for s in seasons:
                yield scrapy.Request(
                    url=self._leistungsdaten_url(href, s),
                    headers=DEFAULT_HEADERS,
                    meta={"parent": parent, "season": s},
                    callback=self.parse,
                    dont_filter=True,
                )

        tables = response.css("table.items")
        if not tables:
            return
        for row in tables[0].css("tbody tr"):
            cells = row.css("td")
            if len(cells) < 9:
                continue
            competition = "".join(cells[1].css("*::text").getall()).strip()
            if not competition:
                continue
            yield {
                "type": "appearance",
                "player_href": player_href,
                "competition": competition,
                "season": season,
                "appearances": _int("".join(cells[2].css("::text").getall())),
                "goals": _int("".join(cells[3].css("::text").getall())),
                "assists": _int("".join(cells[4].css("::text").getall())),
                "yellow_cards": _int("".join(cells[5].css("::text").getall())),
                "second_yellow_cards": _int("".join(cells[6].css("::text").getall())),
                "red_cards": _int("".join(cells[7].css("::text").getall())),
                "minutes": _int("".join(cells[8].css("::text").getall())),
            }
