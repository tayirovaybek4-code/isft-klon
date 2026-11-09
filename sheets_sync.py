"""Deliver committed SQLite application rows to the configured Google Sheet."""

import getpass
import hashlib
import json
import os
import re
import secrets
import sqlite3
import tempfile
import threading
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

GOOGLE_EXEC_URL = re.compile(r"https://script\.google\.com/(?:a/macros/[A-Za-z0-9.-]+/|macros/)s/[A-Za-z0-9_-]+/exec")
SHEET_ID = re.compile(r"[A-Za-z0-9_-]{15,150}")
SECRET_FORMAT = re.compile(r"[A-Za-z0-9_-]{32,128}")
BATCH_SIZE = 25
PENDING = "(sync_target != ? OR synced_version < sync_version)"
PROTOCOL = "isft-sheets-v1"


class SheetsError(ValueError):
    pass


class GoogleContentRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        target = urlsplit(url)
        if target.scheme != "https" or target.netloc != "script.googleusercontent.com":
            raise SheetsError("Apps Script havolasi boshqa manzilga yo‘naltiryapti. /exec URL va ruxsatlarni tekshiring.")
        return super().redirect_request(request, response, code, message, headers, url)


@dataclass(frozen=True)
class SheetsConfig:
    url: str
    secret: str
    sheet_id: str

    @property
    def target(self):
        return hashlib.sha256(f"{self.url}\n{self.sheet_id}".encode()).hexdigest()


def validate_credentials(url, secret):
    if not isinstance(url, str) or not GOOGLE_EXEC_URL.fullmatch(url):
        raise SheetsError("Web app URL https://script.google.com/.../exec ko‘rinishida bo‘lsin.")
    if not isinstance(secret, str) or not SECRET_FORMAT.fullmatch(secret):
        raise SheetsError("Google ulanish kaliti noto‘g‘ri.")


def load_config(path):
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        url, secret, sheet_id = data["url"], data["secret"], data["sheet_id"]
        validate_credentials(url, secret)
        if not isinstance(sheet_id, str) or not SHEET_ID.fullmatch(sheet_id):
            raise SheetsError("Google jadvali ID raqami noto‘g‘ri.")
        return SheetsConfig(url, secret, sheet_id)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise SheetsError("Google sozlamasi o‘qilmadi. Google ulanishini qayta sozlang.") from exc


def send_to_google(url, secret, sheet_id=None, rows=()):
    payload = json.dumps({
        "protocol": PROTOCOL, "secret": secret, "spreadsheet_id": sheet_id, "rows": rows,
    }, ensure_ascii=False).encode()
    request = Request(url, data=payload, method="POST", headers={"Content-Type": "application/json"})
    try:
        with build_opener(GoogleContentRedirect()).open(request, timeout=15) as response:
            result = json.loads(response.read(65_536))
    except HTTPError as exc:
        raise SheetsError(f"Google serveri HTTP {exc.code} qaytardi. Web app ruxsatlarini tekshiring.") from exc
    except (URLError, OSError) as exc:
        raise SheetsError("Google bilan bog‘lanib bo‘lmadi. Internet ulanishini tekshiring.") from exc
    except json.JSONDecodeError as exc:
        raise SheetsError("Google JSON javob qaytarmadi. Web app /exec havolasi va ruxsatlarini tekshiring.") from exc

    if not isinstance(result, dict) or result.get("protocol") != PROTOCOL:
        raise SheetsError("Apps Script javobi mos emas. GoogleSheets.gs faylini qayta joylang.")
    errors = {
        "auth": "Google ulanish kaliti mos kelmadi.",
        "target": "Google jadvali o‘zgargan. Ulanishni qayta sozlang.",
        "header": "Arizalar varag‘i ustunlari mos emas. Birinchi qatorni tekshiring.",
        "busy": "Google jadvali band. Birozdan so‘ng qayta yuboriladi.",
    }
    if result.get("ok") is not True:
        code = result.get("code")
        raise SheetsError(errors.get(code, "Apps Script yozuvni saqlay olmadi.") if isinstance(code, str)
                          else "Apps Script yozuvni saqlay olmadi.")
    returned_id = result.get("spreadsheet_id")
    if not isinstance(returned_id, str) or not SHEET_ID.fullmatch(returned_id):
        raise SheetsError("Google jadvali ID raqami qaytmadi.")
    if sheet_id and returned_id != sheet_id:
        raise SheetsError(errors["target"])
    if result.get("keys") != [row["submission_key"] for row in rows]:
        raise SheetsError("Google barcha yozuvlarni tasdiqlamadi. Qayta yuboriladi.")
    return returned_id


class SheetsSync:
    def __init__(self, path, connect):
        self.connect = connect
        self.signal = threading.Event()
        self.error = ""
        try:
            self.config = load_config(path)
        except SheetsError as exc:
            self.config = None
            self.error = str(exc)

    def start(self):
        if self.config:
            threading.Thread(target=self.run, name="isft-sheets", daemon=True).start()

    def wake(self):
        self.signal.set()

    def status(self):
        with self.connect() as connection:
            target = self.config.target if self.config else ""
            total, pending = connection.execute(f"""
                SELECT COUNT(*), COUNT(CASE WHEN {PENDING} THEN 1 END) FROM applications
            """, (target,)).fetchone()
        return {
            "configured": self.config is not None,
            "synced": total - pending if self.config else 0,
            "pending": pending if self.config else total,
            "error": self.error,
            "sheet_id": self.config.sheet_id if self.config else None,
        }

    def sync_once(self):
        config = self.config
        with self.connect() as connection:
            rows = [dict(row) for row in connection.execute(f"""
                SELECT id, submission_key, sync_version, created_at, first_name, last_name,
                       father_name, phone, birth_date, program, study_type, consent, status
                FROM applications WHERE {PENDING} ORDER BY id LIMIT ?
            """, (config.target, BATCH_SIZE))]
        if not rows:
            return False

        send_to_google(config.url, config.secret, config.sheet_id, rows)
        with self.connect() as connection:
            connection.executemany("""
                UPDATE applications SET synced_version = ?, sync_target = ?
                WHERE id = ? AND sync_version = ?
            """, ((row["sync_version"], config.target, row["id"], row["sync_version"]) for row in rows))
        return True

    def run(self):
        while True:
            self.signal.clear()
            try:
                while self.sync_once():
                    self.error = ""
            except (SheetsError, sqlite3.Error) as exc:
                self.error = str(exc) if isinstance(exc, SheetsError) else "Mahalliy baza vaqtincha band."
                # Wait before retrying even if more applications arrive during the outage.
                threading.Event().wait(30)
                continue
            self.signal.wait(5)


def configure_sheets(path):
    try:
        print("Google Sheets ulanishi. Avval GOOGLE_SHEETS.md faylini oching.\n")
        secret = getpass.getpass("Mavjud ISFT_SYNC_SECRET (yangi kalit uchun Enter): ").strip()
        if not secret:
            secret = secrets.token_urlsafe(32)
            print("\nISFT_SYNC_SECRET qiymatini Google Apps Script sozlamasiga qo‘ying:")
            print(f"\n{secret}\n")
        url = input("Skriptni Deploy qiling va Web app /exec URL manzilini kiriting: ").strip()
        if not url:
            print("Ulanish sozlanmadi.")
            return 1
        validate_credentials(url, secret)
        sheet_id = send_to_google(url, secret)
        # Replace only after the new destination has answered the authenticated check.
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix="sheets.local.", suffix=".tmp", delete=False,
        ) as output:
            temp_path = path.parent / os.path.basename(output.name)
        try:
            temp_path.write_text(json.dumps({"url": url, "secret": secret, "sheet_id": sheet_id}), encoding="utf-8")
            temp_path.replace(path)
        finally:
            temp_path.unlink(missing_ok=True)
        print("Google Sheets ulanishi tekshirildi. Saytni qayta ishga tushiring.")
        return 0
    except (SheetsError, OSError, EOFError, KeyboardInterrupt) as exc:
        print(f"Google ulanishi saqlanmadi. {exc}")
        return 1
