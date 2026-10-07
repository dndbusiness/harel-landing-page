from __future__ import annotations

import re
from datetime import date

from ..model.transaction import BANKER, DIRECT

_DATE_RE = re.compile(r"^(\d{1,2})[/.](\d{1,2})[/.](\d{2}|\d{4})$")
_CHANNEL_RE = re.compile(r"\((?P<c>[יפ])\)")


class ParseError(ValueError):
    pass


def parse_date(text: str) -> date:
    m = _DATE_RE.match(text.strip())
    if not m:
        raise ParseError(f"תאריך לא חוקי: {text!r}")
    d, mo, y = (int(x) for x in m.groups())
    if y < 100:
        y += 2000
    return date(y, mo, d)


def is_date(text: str) -> bool:
    return bool(_DATE_RE.match((text or "").strip()))


def split_channel(description: str) -> tuple[str, str | None]:
    """'(י) העברה' → ('העברה', 'direct'). הסימון נשמר כדגל נפרד."""
    m = _CHANNEL_RE.search(description)
    if not m:
        return description.strip(), None
    channel = DIRECT if m.group("c") == "י" else BANKER
    cleaned = (description[: m.start()] + description[m.end():]).strip()
    return re.sub(r"\s+", " ", cleaned), channel
