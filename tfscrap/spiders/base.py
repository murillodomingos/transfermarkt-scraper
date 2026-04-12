from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from typing import Any

import scrapy

DEFAULT_BASE_URL = "https://www.transfermarkt.com"
DEFAULT_UA = (
    "Mozilla/5.0 (tfscrap/0.1 academic-project SME0829 ICMC-USP; +mailto:contact@example.com)"
)
DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_UA,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class BaseSpider(scrapy.Spider):
    """Common behaviour: read JSONL parents from stdin or -p FILE and dispatch requests."""

    name = "base"

    def __init__(
        self,
        parents: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        season: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.parents_file = parents
        self.base_url = base_url.rstrip("/")
        self.season = season

    def read_parents(self) -> Iterator[dict]:
        stream = open(self.parents_file) if self.parents_file else sys.stdin
        try:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)
        finally:
            if self.parents_file:
                stream.close()

    def start_requests(self) -> Iterator[scrapy.Request]:
        for parent in self.read_parents():
            href = parent.get("href")
            if not href:
                continue
            url = self.base_url + href if href.startswith("/") else href
            yield scrapy.Request(
                url=url,
                headers=DEFAULT_HEADERS,
                meta={"parent": parent},
                callback=self.parse,
            )
