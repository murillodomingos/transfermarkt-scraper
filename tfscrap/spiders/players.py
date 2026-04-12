from __future__ import annotations

import re

import scrapy

from tfscrap.spiders.base import DEFAULT_HEADERS, BaseSpider
from tfscrap.utils import normalize_href, parse_market_value, parse_tm_date


def _clean(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = " ".join(raw.split()).strip()
    return s or None


_DOB_RE = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})(?:\s*\((\d+)\))?")
_HEIGHT_RE = re.compile(r"(\d+)[,\.](\d+)\s*m")


class PlayersSpider(BaseSpider):
    """Yields one item per player, fetching the profile page for enrichment."""

    name = "players"

    def parse(self, response, **kwargs):
        parent = response.meta.get("parent") or {}
        seen: set[str] = set()
        for row in response.css("table.items tbody tr"):
            href = row.css("td.hauptlink a::attr(href)").get()
            if not href or "/profil/spieler/" not in href:
                continue
            canon = normalize_href(href)
            if canon in seen:
                continue
            seen.add(canon)
            url = self.base_url + canon
            yield scrapy.Request(
                url=url,
                headers=DEFAULT_HEADERS,
                meta={"parent": parent, "player_href": canon},
                callback=self.parse_profile,
            )

    def parse_profile(self, response, **kwargs):
        parent = response.meta.get("parent") or {}
        href = response.meta.get("player_href") or normalize_href(response.url)

        name = _clean(" ".join(response.css("h1 *::text").getall()))
        # drop jersey prefix "#9 " if present
        if name:
            name = re.sub(r"^#\d+\s*", "", name).strip()

        # info-table: collect label/value pairs
        info = self._info_table(response)
        dob, age = self._parse_dob_age(info.get("Date of birth/Age:"))
        height_cm = self._parse_height_cm(info.get("Height:"))
        nationality = info.get("Citizenship:")
        position = info.get("Position:")
        foot = info.get("Foot:")
        joined = parse_tm_date(info.get("Joined:"))
        contract_until = parse_tm_date(info.get("Contract expires:"))

        mv_parts = response.css("a.data-header__market-value-wrapper *::text").getall()[:3]
        mv_raw = "".join(p.strip() for p in mv_parts) if mv_parts else None
        market_value = parse_market_value(mv_raw)

        yield {
            "type": "player",
            "name": name,
            "href": href,
            "club_href": parent.get("href"),
            "dob": dob,
            "age": age,
            "nationality": nationality,
            "position": position,
            "foot": foot,
            "height_cm": height_cm,
            "joined": joined,
            "contract_until": contract_until,
            "market_value": market_value,
        }

    @staticmethod
    def _info_table(response) -> dict[str, str]:
        labels = response.css(".info-table span.info-table__content--regular::text").getall()
        value_nodes = response.css(".info-table span.info-table__content--bold")
        values = [
            _clean(" ".join(node.css("*::text").getall()))
            for node in value_nodes
        ]
        out = {}
        for label, value in zip(labels, values, strict=False):
            key = _clean(label) or ""
            if key:
                out[key] = value
        return out

    @staticmethod
    def _parse_dob_age(raw: str | None):
        if not raw:
            return None, None
        m = _DOB_RE.search(raw)
        if not m:
            return None, None
        dob = parse_tm_date(m.group(1))
        age = int(m.group(2)) if m.group(2) else None
        return dob, age

    @staticmethod
    def _parse_height_cm(raw: str | None):
        if not raw:
            return None
        m = _HEIGHT_RE.search(raw)
        if not m:
            return None
        meters = int(m.group(1))
        cm_part = int(m.group(2))
        # "1,95 m" → 195 cm
        return meters * 100 + (cm_part if cm_part < 100 else 0)
