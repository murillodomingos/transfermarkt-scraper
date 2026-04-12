from __future__ import annotations

from tfscrap.spiders.base import BaseSpider
from tfscrap.utils import normalize_href


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

    def parse(self, response, **kwargs):
        parent = response.meta.get("parent") or {}
        player_href = normalize_href(parent.get("href")) or normalize_href(response.url)
        season = response.css("select[name=saison] option[selected]::attr(value)").get()

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
