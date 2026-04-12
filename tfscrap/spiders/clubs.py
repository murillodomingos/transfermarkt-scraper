from __future__ import annotations

from tfscrap.spiders.base import BaseSpider
from tfscrap.utils import normalize_href, parse_market_value


def _num(raw: str | None, cast=int):
    if raw is None:
        return None
    s = raw.strip().replace(",", ".")
    if not s or s == "-":
        return None
    try:
        return cast(s)
    except ValueError:
        return None


class ClubsSpider(BaseSpider):
    """Extract the 20-ish clubs listed on a competition's /startseite/wettbewerb page."""

    name = "clubs"

    def parse(self, response, **kwargs):
        parent = response.meta.get("parent") or {}
        competition_href = normalize_href(parent.get("href")) or normalize_href(response.url)

        # The first table.items on a competition page is the clubs overview:
        # columns: [club-logo, name, squad_size, avg_age, foreigners, avg_value, total_value].
        first_table = response.css("table.items")[0] if response.css("table.items") else None
        if first_table is None:
            return
        rows = first_table.xpath(".//tbody/tr")
        for row in rows:
            name_link = row.css("td.hauptlink a")
            href = normalize_href(name_link.attrib.get("href"))
            name = name_link.css("::text").get()
            if not href or not name:
                continue
            cells = row.css("td")
            squad_size = _num("".join(cells[2].css("::text").getall()).strip()) if len(cells) > 2 else None
            avg_age = _num("".join(cells[3].css("::text").getall()).strip(), cast=float) if len(cells) > 3 else None
            total_mv = (
                parse_market_value("".join(cells[6].css("::text").getall()).strip())
                if len(cells) > 6
                else None
            )
            yield {
                "type": "club",
                "name": name.strip(),
                "href": href,
                "competition_href": competition_href,
                "squad_size": squad_size,
                "avg_age": avg_age,
                "total_market_value": total_mv,
            }
