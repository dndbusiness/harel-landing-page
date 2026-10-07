"""תיקיית לקוח: הצפנה במנוחה, לוג גישה ומחיקה מסודרת (סעיף 11).

הצפנה: Fernet (ספריית cryptography). המפתח לא נשמר בתיקיית הלקוח — הוא נלקח
ממשתנה הסביבה OSHSIM_KEY או מקובץ שהנתיב שלו ב-OSHSIM_KEY_FILE.
בלי מפתח הקבצים נשמרים גלויים, והמערכת מתריעה על כך בכל ריצה.
"""
from __future__ import annotations

import getpass
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path


def generate_key() -> str:
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


class Workspace:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._fernet = self._load_key()

    # ---------- מפתח ----------
    @staticmethod
    def _load_key():
        key = os.environ.get("OSHSIM_KEY")
        kf = os.environ.get("OSHSIM_KEY_FILE")
        if not key and kf and Path(kf).exists():
            key = Path(kf).read_text().strip()
        if not key:
            return None
        from cryptography.fernet import Fernet
        return Fernet(key.encode())

    @property
    def encrypted(self) -> bool:
        return self._fernet is not None

    # ---------- לוג ----------
    def log(self, action: str, target: str) -> None:
        entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "user": getpass.getuser(), "action": action, "target": target}
        with (self.root / "access.log").open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ---------- קריאה/כתיבה ----------
    def path(self, name: str) -> Path:
        return self.root / name

    def write_json(self, name: str, data) -> Path:
        raw = json.dumps(data, ensure_ascii=False, indent=1).encode("utf-8")
        if self._fernet:
            p = self.root / (name + ".enc")
            p.write_bytes(self._fernet.encrypt(raw))
            plain = self.root / name
            if plain.exists():
                shred(plain)
        else:
            p = self.root / name
            p.write_bytes(raw)
        self.log("write", p.name)
        return p

    def read_json(self, name: str):
        enc, plain = self.root / (name + ".enc"), self.root / name
        if enc.exists():
            if not self._fernet:
                raise PermissionError(f"{enc.name} מוצפן — חסר OSHSIM_KEY")
            data = self._fernet.decrypt(enc.read_bytes())
            self.log("read", enc.name)
        elif plain.exists():
            data = plain.read_bytes()
            self.log("read", plain.name)
        else:
            raise FileNotFoundError(f"אין {name} בתיקיית הלקוח — הריצו קודם ingest")
        return json.loads(data.decode("utf-8"))

    def purge(self) -> int:
        """מחיקה מסודרת של כל קבצי הלקוח (דריסה ואז מחיקה). לוג הגישה נשמר אחרון ונמחק גם הוא."""
        n = 0
        for p in sorted(self.root.rglob("*"), key=lambda p: -len(p.parts)):
            if p.is_file():
                shred(p)
                n += 1
            elif p.is_dir():
                p.rmdir()
        self.root.rmdir()
        return n


def shred(p: Path) -> None:
    """דריסה בנתונים אקראיים ואז מחיקה. בדיסקי SSD/מערכות קבצים עם העתקה אין לזה
    ערובה מלאה — לכן ההצפנה במנוחה היא ההגנה העיקרית."""
    size = p.stat().st_size
    with p.open("r+b") as f:
        f.write(secrets.token_bytes(size))
        f.flush()
        os.fsync(f.fileno())
    p.unlink()
