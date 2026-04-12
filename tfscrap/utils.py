from __future__ import annotations

import re
from datetime import date, datetime
from urllib.parse import urlparse

from dateutil import parser as _date_parser

_MISSING = {"-", "", "n/a", "?", "unknown"}

_VALUE_RE = re.compile(
    r"""
    ^\s*
    [^\d\-.,]*          # currency symbol / prefix
    (?P<num>\d+(?:[.,]\d+)?)
    \s*
    (?P<unit>bn|m|k)?    # billions / millions / thousands
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


def parse_market_value(raw: str | None) -> int | None:
    """Parse Transfermarkt market-value strings into integer euros.

    Examples: "€12.50m" -> 12_500_000, "€800k" -> 800_000, "-" -> None.
    """
    if raw is None:
        return None
    s = raw.strip()
    if s.lower() in _MISSING:
        return None
    m = _VALUE_RE.match(s)
    if not m:
        return None
    num = float(m.group("num").replace(",", "."))
    unit = (m.group("unit") or "").lower()
    if unit == "bn":
        num *= 1_000_000_000
    elif unit == "m":
        num *= 1_000_000
    elif unit == "k":
        num *= 1_000
    return int(round(num))


_DATE_FORMATS = ("%b %d, %Y", "%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y")


def parse_tm_date(raw: str | None) -> date | None:
    """Parse a Transfermarkt-style date into a `date`; return None if unparseable."""
    if raw is None:
        return None
    s = raw.strip()
    if s.lower() in _MISSING:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    try:
        return _date_parser.parse(s, dayfirst=True).date()
    except (ValueError, OverflowError):
        return None


def normalize_href(raw: str | None) -> str | None:
    """Strip host, query, fragment from a Transfermarkt URL, keeping only the path."""
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    parsed = urlparse(s)
    path = parsed.path or s
    if not path.startswith("/"):
        path = "/" + path
    return path or None
