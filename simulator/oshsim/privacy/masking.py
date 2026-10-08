"""הסתרת מזהים בפלטים (סעיף 11) — מציגים רק את 4 הספרות האחרונות."""
from __future__ import annotations

import re

_LONG_NUM = re.compile(r"\d[\d\-/ ]{6,}\d")


def mask_account(value: str, keep: int = 4) -> str:
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return ""
    return "•" * max(0, len(digits) - keep) + digits[-keep:]


def mask_text(text: str) -> str:
    """כל רצף ספרות ארוך (חשבון/כרטיס/ת"ז) בתוך טקסט חופשי — מוסתר."""
    return _LONG_NUM.sub(lambda m: mask_account(m.group(0)), text or "")
