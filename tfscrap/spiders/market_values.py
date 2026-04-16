from __future__ import annotations

import json
import re
from collections.abc import Iterator

import scrapy

from tfscrap.spiders.base import DEFAULT_HEADERS, BaseSpider
from tfscrap.utils import normalize_href, parse_tm_date

_PLAYER_ID_RE = re.compile(r"/spieler/(\d+)")


class MarketValuesSpider(BaseSpider):
    """Fetch JSON market value history from ceapi and emit one item per snapshot."""

    name = "market_values"

    def api_url_for(self, parent: dict) -> str | None:
        href = parent.get("href") or ""
        m = _PLAYER_ID_RE.search(href)
        if not m:
            return None
        return f"{self.base_url}/ceapi/marketValueDevelopment/graph/{m.group(1)}"

    def start_requests(self) -> Iterator[scrapy.Request]:
        for parent in self.read_parents():
            url = self.api_url_for(parent)
            if not url:
                continue
            yield scrapy.Request(
                url=url,
                headers={**DEFAULT_HEADERS, "Accept": "application/json"},
                meta={"parent": parent},
                callback=self.parse,
            )

    def parse(self, response, **kwargs):
        parent = response.meta.get("parent") or {}
        player_href = normalize_href(parent.get("href"))
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return
        for entry in data.get("list", []):
            yield {
                "type": "market_value",
                "player_href": player_href,
                "date": parse_tm_date(entry.get("datum_mw")),
                "market_value": entry.get("y"),
                "club_name": entry.get("verein"),
            }
