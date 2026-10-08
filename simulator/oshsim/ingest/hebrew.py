"""טיפול בטקסט עברי שנשלף מ-PDF בסדר חזותי (הפוך)."""
from __future__ import annotations

import re

_HEB = re.compile(r"[֐-׿]")
# רצף "משמאל לימין": ספרות, לטינית, ותווי פיסוק שבין ספרות
_LTR_RUN = re.compile(r"[0-9A-Za-z](?:[0-9A-Za-z.,/:%\-]*[0-9A-Za-z])?")
_MIRROR = str.maketrans("()[]{}<>", ")(][}{><")


def has_hebrew(s: str) -> bool:
    return bool(_HEB.search(s or ""))


def visual_to_logical(s: str) -> str:
    """'הרוכשמ )י(' → '(י) משכורת'. מחרוזת בלי עברית חוזרת כמו שהיא."""
    if not has_hebrew(s):
        return s
    rev = s[::-1].translate(_MIRROR)
    return _LTR_RUN.sub(lambda m: m.group(0)[::-1], rev)


def normalize_spaces(s: str) -> str:
    s = s.replace("‏", "").replace("‎", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()
