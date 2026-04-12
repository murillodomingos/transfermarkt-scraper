from __future__ import annotations

from tfscrap.spiders.base import BaseSpider
from tfscrap.utils import normalize_href


class CompetitionsSpider(BaseSpider):
    """Enrich competition seeds with metadata from each /startseite/wettbewerb/ page."""

    name = "competitions"

    def parse(self, response, **kwargs):
        parent = response.meta.get("parent") or {}
        name = response.css("h1::text").get(default="").strip()
        # Country is the first breadcrumb link on competition pages.
        country = (
            response.css(".data-header__club a::text").get()
            or response.css("img.data-header__box__flag::attr(alt)").get()
            or ""
        ).strip()
        season = response.css("select[name=saison_id] option[selected]::attr(value)").get()
        href = normalize_href(parent.get("href")) or normalize_href(response.url)
        yield {
            "type": "competition",
            "name": name or None,
            "country": country or None,
            "season": season,
            "href": href,
        }
