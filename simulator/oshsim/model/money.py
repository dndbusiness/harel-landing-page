"""כסף כמספר שלם באגורות. אין float במסלול הכסף.

כל המרה מטקסט או מאחוז עוברת דרך הפונקציות כאן, כדי שיהיה מקום אחד לבדוק.
"""
from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

Agorot = int

# מינוס יכול להופיע כמקף רגיל, כמינוס יוניקוד, או בסוף המספר (טקסט RTL הפוך)
_MINUS_CHARS = "-−‒–—"
_AMOUNT_RE = re.compile(
    rf"^\s*(?P<lead>[{_MINUS_CHARS}])?\s*₪?\s*"
    r"(?P<num>\d{1,3}(?:,\d{3})*|\d+)(?:\.(?P<frac>\d{1,2}))?"
    rf"\s*₪?\s*(?P<trail>[{_MINUS_CHARS}])?\s*$"
)


class MoneyParseError(ValueError):
    pass


def parse_amount(text: str) -> Agorot:
    """'−1,234.56' / '1,234.56-' / '1234.5' → אגורות (int)."""
    if text is None:
        raise MoneyParseError("סכום חסר")
    t = text.replace("‏", "").replace("‎", "").replace("\xa0", " ").strip()
    m = _AMOUNT_RE.match(t)
    if not m:
        raise MoneyParseError(f"לא ניתן לפרש סכום: {text!r}")
    if m.group("lead") and m.group("trail"):
        raise MoneyParseError(f"סימן מינוס כפול: {text!r}")
    whole = int(m.group("num").replace(",", ""))
    frac = (m.group("frac") or "0").ljust(2, "0")
    value = whole * 100 + int(frac)
    if m.group("lead") or m.group("trail"):
        value = -value
    return value


def looks_like_amount(text: str) -> bool:
    try:
        parse_amount(text)
        return True
    except MoneyParseError:
        return False


def to_decimal(agorot: Agorot) -> Decimal:
    """אגורות → Decimal בשקלים (לכתיבה ל-Excel ולתצוגה)."""
    return (Decimal(agorot) / Decimal(100)).quantize(Decimal("0.01"))


def from_decimal(value: Decimal | str | int) -> Agorot:
    """Decimal/מחרוזת בשקלים → אגורות, עיגול חצי למעלה (כמו בנק)."""
    if isinstance(value, float):
        raise TypeError("float אסור במסלול כסף")
    try:
        d = Decimal(str(value))
    except InvalidOperation as e:
        raise MoneyParseError(f"ערך לא חוקי: {value!r}") from e
    return int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def scale(agorot: Agorot, factor: Decimal | str) -> Agorot:
    """הכפלה באחוז/מקדם עם עיגול לאגורה."""
    if isinstance(factor, float):
        raise TypeError("float אסור במסלול כסף")
    f = Decimal(str(factor))
    return int((Decimal(agorot) * f).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def fmt(agorot: Agorot | None, sign: bool = True) -> str:
    """'-1,234.56' — תצוגה בלבד."""
    if agorot is None:
        return ""
    neg = agorot < 0
    a = abs(agorot)
    s = f"{a // 100:,}.{a % 100:02d}"
    return f"-{s}" if (neg and sign) else s
