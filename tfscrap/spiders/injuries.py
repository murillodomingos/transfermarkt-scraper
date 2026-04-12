from __future__ import annotations

import re

from tfscrap.spiders.base import BaseSpider
from tfscrap.utils import normalize_href, parse_tm_date

_DAYS_RE = re.compile(r"(\d+)")


def _int(raw: str | None) -> int | None:
    if raw is None:
        return None
    m = _DAYS_RE.search(raw)
    return int(m.group(1)) if m else None


class InjuriesSpider(BaseSpider):
    """One item per injury record on /verletzungen/spieler/<id>."""

    name = "injuries"

    def parse(self, response, **kwargs):
        parent = response.meta.get("parent") or {}
        player_href = normalize_href(parent.get("href")) or normalize_href(response.url)

        tables = response.css("table.items")
        if not tables:
            return
        for row in tables[0].css("tbody tr"):
            cells = row.css("td")
            if len(cells) < 6:
                continue
            values = ["".join(c.css("::text").getall()).strip() for c in cells]
            yield {
                "type": "injury",
                "player_href": player_href,
                "season": values[0] or None,
                "injury": values[1] or None,
                "from": parse_tm_date(values[2]),
                "until": parse_tm_date(values[3]),
                "days_out": _int(values[4]),
                "games_missed": _int(values[5]),
            }
