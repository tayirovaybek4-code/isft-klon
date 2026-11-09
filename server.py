import argparse
import base64
import binascii
import getpass
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sqlite3
import sys
import threading
import time
import uuid
import webbrowser
from contextlib import closing, contextmanager
from datetime import date, datetime, timedelta
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from sheets_sync import SheetsSync, configure_sheets

ROOT = Path(__file__).resolve().parent
DB = ROOT / "isft.db"
STATIC = ROOT / "static"
UPLOAD = ROOT / "uploads"
PROGRAMS = (
    "Axborot tizimlari va texnologiyalari", "Iqtisodiyot", "Marketing",
    "Bank ishi", "Axborot xavfsizligi", "Xalqaro munosabatlar", "Menejment",
    "Biznes va menejment", "Moliya sohasida boshqaruv",
    "Buxgalteriya hisobi va moliya", "Xorijiy til va adabiyoti",
    "Maktabgacha ta’lim", "Boshlang‘ich ta’lim", "Pedagogika", "Psixologiya",
    "Filologiya va tillarni o‘qitish (Ingliz tili)",
)
DEFAULT_MENU = (
    ("Bosh sahifa", "/"), ("Universitet", "/about.html"),
    ("Yo‘nalishlar", "/programs.html"), ("Yangiliklar", "/news.html"),
    ("Qabul", "/apply.html"), ("Aloqa", "/contact.html"),
)
DEFAULT_SETTINGS = {
    "site_name": "ISFT Universiteti",
    "hero_title": "ISFT Universiteti",
    "hero_subtitle": "Ta’lim yo‘nalishlari bilan tanishing va onlayn ariza topshiring.",
    "contact_phone": "",
    "contact_address": "",
    "contact_email": "",
    "footer_text": "© ISFT Universiteti",
}
STATUSES = ("Yangi", "Ko‘rib chiqilmoqda", "Qabul qilingan", "Rad etilgan")
CONTENT_KINDS = ("E’lon", "Yangilik", "Sahifa")
APPLICATION_FIELDS = (
    "id, first_name, last_name, father_name, phone, birth_date, program, "
    "study_type, status, created_at, program_id, consent"
)
MIME_TYPES = {
    ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8", ".jpg": "image/jpeg",
    ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
}
SESSION_SECONDS = 8 * 3600
MAX_BODY = 6 * 1024 * 1024
LOGIN_ATTEMPTS = {}
LOGIN_LOCK = threading.Lock()


class ApiError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


@contextmanager
def connect():
    with closing(sqlite3.connect(DB, timeout=10)) as connection, connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection


def now():
    return datetime.now().isoformat(timespec="seconds")


def audit(connection, action):
    connection.execute("INSERT INTO audit(action, created_at) VALUES (?, ?)", (action, now()))


def password_digest(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310_000).hex()


def first_admin_password():
    password = os.getenv("ADMIN_PASSWORD")
    if password is not None:
        if 12 <= len(password) <= 256:
            return password
        raise SystemExit("ADMIN_PASSWORD 12–256 belgidan iborat bo‘lsin.")
    if not sys.stdin.isatty():
        raise SystemExit("Admin parolini terminalda belgilang yoki ADMIN_PASSWORD kiriting.")
    print("Birinchi sozlash. Login — admin. Parol yozayotganda belgilar ko‘rinmaydi.")
    while True:
        password = getpass.getpass("Yangi admin paroli (kamida 12 belgi): ")
        if not 12 <= len(password) <= 256:
            print("12–256 belgidan iborat parol kiriting.")
        elif password != getpass.getpass("Parolni qayta kiriting: "):
            print("Parollar mos kelmadi.")
        else:
            return password


def init():
    UPLOAD.mkdir(exist_ok=True)
    with connect() as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, username TEXT UNIQUE, salt TEXT, digest TEXT
            );
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
                father_name TEXT, phone TEXT NOT NULL, birth_date TEXT, program TEXT NOT NULL,
                study_type TEXT, status TEXT DEFAULT 'Yangi', created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL,
                body TEXT NOT NULL, published INTEGER DEFAULT 0, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS programs (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                description TEXT DEFAULT '', active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY, action TEXT, created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY, label TEXT NOT NULL, url TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY, filename TEXT NOT NULL, original_name TEXT NOT NULL,
                mime TEXT NOT NULL, size INTEGER NOT NULL, created_at TEXT NOT NULL
            );
        """)
        connection.execute("BEGIN IMMEDIATE")
        if not connection.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            password = first_admin_password()
            salt = secrets.token_hex(16)
            connection.execute(
                "INSERT INTO users(username, salt, digest) VALUES (?, ?, ?)",
                ("admin", salt, password_digest(password, salt)),
            )
            if not connection.execute("SELECT 1 FROM programs LIMIT 1").fetchone():
                connection.executemany("INSERT INTO programs(name) VALUES (?)", ((name,) for name in PROGRAMS))
            if not connection.execute("SELECT 1 FROM menu LIMIT 1").fetchone():
                connection.executemany(
                    "INSERT INTO menu(label, url, position) VALUES (?, ?, ?)",
                    ((label, url, position) for position, (label, url) in enumerate(DEFAULT_MENU)),
                )
            connection.executemany(
                "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", DEFAULT_SETTINGS.items(),
            )
        migrate(connection)


def migrate(connection):
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(applications)")}
    additions = {
        "program_id": "INTEGER REFERENCES programs(id) ON DELETE SET NULL",
        "consent": "INTEGER",
        "submission_key": "TEXT",
        "sync_version": "INTEGER NOT NULL DEFAULT 1",
        "synced_version": "INTEGER NOT NULL DEFAULT 0",
        "sync_target": "TEXT NOT NULL DEFAULT ''",
    }
    for name, definition in additions.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE applications ADD COLUMN {name} {definition}")
    if "program_id" not in columns:
        # Only link older records when the saved name identifies exactly one program.
        connection.execute("""
            UPDATE applications SET program_id = (
                SELECT MIN(programs.id) FROM programs WHERE programs.name = applications.program
                HAVING COUNT(*) = 1
            )
        """)
    if "submission_key" not in columns:
        connection.execute("UPDATE applications SET submission_key = lower(hex(randomblob(16)))")
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS applications_key ON applications(submission_key)")
    connection.execute("CREATE INDEX IF NOT EXISTS applications_program ON applications(program_id)")
    content_columns = {row["name"] for row in connection.execute("PRAGMA table_info(content)")}
    if "page" not in content_columns:
        connection.execute("ALTER TABLE content ADD COLUMN page TEXT NOT NULL DEFAULT ''")


def string_field(data, key, label, max_length, min_length=0):
    value = data.get(key, "")
    if not isinstance(value, str) or not min_length <= len(value.strip()) <= max_length:
        raise ApiError(f"{label} maydonini tekshiring.")
    return value.strip()


def boolean_field(data, key, default=False):
    value = data.get(key, default)
    if type(value) is bool or (type(value) is int and value in (0, 1)):
        return int(value)
    raise ApiError("Belgilash maydoni noto‘g‘ri.")


def menu_url(value):
    if not re.fullmatch(r"/[a-zA-Z0-9_/?=&.%-]{0,199}", value) or value.startswith("//"):
        raise ApiError("Havola ichki sahifaga olib borishi kerak, masalan /about.html.")
    return value


def menu_position(value):
    if type(value) is not int or not -10_000 <= value <= 10_000:
        raise ApiError("Tartib raqami −10000 va 10000 oralig‘ida bo‘lsin.")
    return value


def program_name(connection, name, item_id=0):
    duplicate = connection.execute(
        "SELECT 1 FROM programs WHERE name = ? COLLATE NOCASE AND id != ?", (name, item_id),
    ).fetchone()
    if duplicate:
        raise ApiError("Bunday nomli yo‘nalish bor.", 409)
    return name


def content_fields(data, old=None):
    old = old or {}
    kind = data.get("kind", old.get("kind"))
    page = data.get("page", old.get("page", ""))
    if kind not in CONTENT_KINDS:
        raise ApiError("Material turini tanlang.")
    if page not in ("", "about", "contact"):
        raise ApiError("Material chiqadigan sahifani tanlang.")
    return {"kind": kind, "page": page if kind == "Sahifa" else ""}


def application_input(data):
    fields = (
        ("first_name", "Ism", 100, 2), ("last_name", "Familiya", 100, 2),
        ("father_name", "Otasining ismi", 100, 0), ("phone", "Telefon", 22, 9),
        ("birth_date", "Tug‘ilgan sana", 10, 0), ("study_type", "Ta’lim shakli", 60, 0),
    )
    values = {key: string_field(data, key, label, size, minimum) for key, label, size, minimum in fields}
    phone = values["phone"]
    if not re.fullmatch(r"\+?[0-9 ()-]+", phone) or not 9 <= len(re.findall(r"[0-9]", phone)) <= 15:
        raise ApiError("Telefon raqamini tekshiring. Masalan, +998901234567.")
    if values["birth_date"]:
        try:
            birthday = date.fromisoformat(values["birth_date"])
            if birthday.isoformat() != values["birth_date"] or birthday > date.today():
                raise ValueError
        except ValueError as exc:
            raise ApiError("Tug‘ilgan sanani tekshiring.") from exc
    return values


def add_application(data):
    values = application_input(data)
    request_key = data.get("request_id")
    if request_key is not None and (
        not isinstance(request_key, str) or not re.fullmatch(r"[0-9a-f]{32}", request_key)
    ):
        raise ApiError("Ariza identifikatori noto‘g‘ri.")
    consent = data.get("consent")
    if (request_key is not None or "consent" in data) and consent is not True:
        raise ApiError("Arizani yuborish uchun rozilikni belgilang.")
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if request_key:
            previous = connection.execute(
                "SELECT id FROM applications WHERE submission_key = ?", (request_key,),
            ).fetchone()
            if previous:
                return 200, previous["id"]
        if "program_id" in data:
            program_id = data["program_id"]
            if type(program_id) is not int or not 1 <= program_id <= 2**63 - 1:
                raise ApiError("Yo‘nalishni tanlang.")
            program = connection.execute(
                "SELECT id, name FROM programs WHERE id = ? AND active = 1", (program_id,),
            ).fetchone()
        else:
            name = string_field(data, "program", "Yo‘nalish", 200, 1)
            program = connection.execute(
                "SELECT id, name FROM programs WHERE name = ? AND active = 1 ORDER BY id LIMIT 1", (name,),
            ).fetchone()
        if not program:
            raise ApiError("Yo‘nalish mavjud emas. Ro‘yxatni yangilab, qayta tanlang.")
        result = connection.execute("""
            INSERT INTO applications(
                first_name, last_name, father_name, phone, birth_date, study_type,
                program, program_id, created_at, submission_key, consent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (*values.values(), program["name"], program["id"], now(),
              request_key or uuid.uuid4().hex, 1 if consent else None))
    return 201, result.lastrowid


def dashboard(connection):
    connection.execute("BEGIN")
    today = date.today()
    start = today - timedelta(days=29)
    statuses = dict(connection.execute("SELECT status, COUNT(*) FROM applications GROUP BY status"))
    counts_by_day = dict(connection.execute("""
        SELECT substr(created_at, 1, 10), COUNT(*) FROM applications
        WHERE created_at >= ? AND created_at < ? GROUP BY substr(created_at, 1, 10)
    """, (start.isoformat(), (today + timedelta(days=1)).isoformat())))
    ranks = connection.execute("""
        SELECT p.name, COUNT(a.id) AS count, 0 AS archived
        FROM programs p LEFT JOIN applications a ON a.program_id = p.id GROUP BY p.id
        UNION ALL
        SELECT program, COUNT(*), 1 FROM applications WHERE program_id IS NULL GROUP BY program
        ORDER BY count DESC, archived, name
    """).fetchall()
    dates = [(start + timedelta(days=index)).isoformat() for index in range(30)]
    return {
        "total": sum(statuses.values()),
        "today": counts_by_day.get(today.isoformat(), 0),
        "statuses": statuses,
        "ranks": [dict(row) for row in ranks],
        "days": [{"day": day, "count": counts_by_day.get(day, 0)} for day in dates],
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send(self, status, obj, content_type="application/json; charset=utf-8", headers=None):
        data = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
        )
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def dispatch(self, handler):
        try:
            handler(urlsplit(self.path).path)
        except ApiError as exc:
            self.send(exc.status, {"error": str(exc)})
        except UnicodeError:
            self.send(400, {"error": "Matn kodlanishi noto‘g‘ri."})
        except sqlite3.Error:
            logging.exception("SQLite xatosi")
            self.send(503, {"error": "Baza bilan bog‘lanishda xato. Bir ozdan keyin urinib ko‘ring."})
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        self.dispatch(self.get)

    def do_HEAD(self):
        self.dispatch(self.get)

    def do_POST(self):
        self.dispatch(self.post)

    def do_PATCH(self):
        self.dispatch(self.patch)

    def do_DELETE(self):
        self.dispatch(self.delete)

    def session_token(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except CookieError:
            return None
        token = cookie.get("sid")
        return hashlib.sha256(token.value.encode()).hexdigest() if token else None

    def session(self):
        token = self.session_token()
        if not token:
            return None
        with connect() as connection:
            return connection.execute(
                "SELECT csrf FROM sessions WHERE token_hash = ? AND expires > ?", (token, time.time()),
            ).fetchone()

    def require(self, write=False):
        session = self.session()
        if not session:
            raise ApiError("Administrator sifatida kiring.", 401)
        if write and self.headers.get("X-CSRF-Token") != session["csrf"]:
            raise ApiError("Sessiya tekshiruvi muvaffaqiyatsiz. Sahifani yangilang.", 403)

    def payload(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= MAX_BODY or self.headers.get_content_type() != "application/json":
                raise ValueError
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, RecursionError) as exc:
            raise ApiError("Yuborilgan ma’lumot formati yoki hajmi noto‘g‘ri.") from exc
        return data

    def get(self, path):
        if path == "/api/session":
            session = self.session()
            return self.send(200, {"logged_in": bool(session), "csrf": session["csrf"] if session else None})
        if path.startswith("/api/"):
            public = path.startswith("/api/public/")
            if not public:
                self.require()
            if path == "/api/sheets":
                return self.send(200, self.server.sheets.status())
            with connect() as connection:
                return self.send(200, self.read_data(connection, path))
        if path.startswith("/media/"):
            filename = path.removeprefix("/media/")
            if not re.fullmatch(r"[a-f0-9]{32}\.(png|jpg|webp|gif)", filename):
                raise ApiError("Rasm topilmadi.", 404)
            with connect() as connection:
                if not connection.execute("SELECT 1 FROM media WHERE filename = ?", (filename,)).fetchone():
                    raise ApiError("Rasm topilmadi.", 404)
            return self.send_file(UPLOAD / filename)
        file = (STATIC / path.lstrip("/")).resolve() if path != "/" else STATIC / "index.html"
        if STATIC not in file.parents:
            raise ApiError("Sahifa topilmadi.", 404)
        self.send_file(file)

    def send_file(self, file):
        content_type = MIME_TYPES.get(file.suffix.lower())
        if not content_type:
            raise ApiError("Sahifa topilmadi.", 404)
        try:
            content = file.read_bytes()
        except (FileNotFoundError, IsADirectoryError):
            raise ApiError("Sahifa topilmadi.", 404) from None
        self.send(200, content, content_type)

    def read_data(self, connection, path):
        if path in ("/api/settings", "/api/public/settings"):
            settings = dict(DEFAULT_SETTINGS)
            settings.update({
                row["key"]: row["value"] for row in connection.execute("SELECT key, value FROM settings")
                if row["key"] in DEFAULT_SETTINGS
            })
            return settings
        if path == "/api/dashboard":
            return dashboard(connection)
        queries = {
            "/api/public/programs": "SELECT id, name, description FROM programs WHERE active = 1 ORDER BY id",
            "/api/public/menu": "SELECT id, label, url, position FROM menu WHERE active = 1 ORDER BY position, id",
            "/api/public/content": "SELECT * FROM content WHERE published = 1 ORDER BY id DESC",
            "/api/applications": f"SELECT {APPLICATION_FIELDS} FROM applications ORDER BY id DESC",
            "/api/programs": "SELECT * FROM programs ORDER BY id",
            "/api/content": "SELECT * FROM content ORDER BY id DESC",
            "/api/menu": "SELECT * FROM menu ORDER BY position, id",
            "/api/media": "SELECT * FROM media ORDER BY id DESC",
            "/api/audit": "SELECT * FROM audit ORDER BY id DESC LIMIT 100",
        }
        if path not in queries:
            raise ApiError("API topilmadi.", 404)
        return [dict(row) for row in connection.execute(queries[path])]

    def session_cookie(self, value, lifetime):
        secure = "; Secure" if os.getenv("ISFT_HTTPS") == "1" else ""
        return {"Set-Cookie": f"sid={value}; HttpOnly; SameSite=Strict; Path=/; Max-Age={lifetime}{secure}"}

    def login(self, data):
        username = string_field(data, "username", "Login", 80, 1)
        password = data.get("password")
        if not isinstance(password, str) or not 1 <= len(password) <= 256:
            raise ApiError("Login yoki parol xato.", 401)
        ip = self.client_address[0]
        current_time = time.time()
        with LOGIN_LOCK:
            attempts = [moment for moment in LOGIN_ATTEMPTS.get(ip, []) if current_time - moment < 900]
            if len(attempts) >= 8:
                raise ApiError("Ko‘p urinish bo‘ldi. 15 daqiqadan keyin qayta urining.", 429)
            LOGIN_ATTEMPTS[ip] = [*attempts, current_time]
        with connect() as connection:
            user = connection.execute("SELECT salt, digest FROM users WHERE username = ?", (username,)).fetchone()
        salt = user["salt"] if user else "0" * 32
        digest = password_digest(password, salt)
        if not user or not hmac.compare_digest(digest, user["digest"]):
            raise ApiError("Login yoki parol xato.", 401)
        sid, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
        with connect() as connection:
            connection.execute(
                "DELETE FROM sessions WHERE expires <= ? OR token_hash = ?", (current_time, self.session_token()),
            )
            connection.execute(
                "INSERT INTO sessions(token_hash, csrf, expires) VALUES (?, ?, ?)",
                (hashlib.sha256(sid.encode()).hexdigest(), csrf, current_time + SESSION_SECONDS),
            )
        with LOGIN_LOCK:
            LOGIN_ATTEMPTS.pop(ip, None)
        self.send(200, {"ok": True, "csrf": csrf}, headers=self.session_cookie(sid, SESSION_SECONDS))

    def post(self, path):
        if path == "/api/login":
            return self.login(self.payload())
        if path == "/api/apply":
            status, application_id = add_application(self.payload())
            self.server.sheets.wake()
            return self.send(status, {"ok": True, "application_id": application_id})
        self.require(write=True)
        data = self.payload()
        if path == "/api/logout":
            with connect() as connection:
                connection.execute("DELETE FROM sessions WHERE token_hash = ?", (self.session_token(),))
            return self.send(200, {"ok": True}, headers=self.session_cookie("", 0))
        if path == "/api/media":
            return self.upload_media(data)
        with connect() as connection:
            if path == "/api/settings":
                if not data or any(key not in DEFAULT_SETTINGS for key in data):
                    raise ApiError("Sozlamalar noto‘g‘ri.")
                settings = {
                    key: string_field(data, key, "Sozlama", 1000) for key in data
                }
                connection.executemany("""
                    INSERT INTO settings(key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """, settings.items())
                audit(connection, "Sayt sozlamalari yangilandi")
                result, status = {"ok": True}, 200
            else:
                connection.execute("BEGIN IMMEDIATE")
                result, status = {"id": self.add_record(connection, path, data)}, 201
        self.send(status, result)

    def add_record(self, connection, path, data):
        if path == "/api/menu":
            label = string_field(data, "label", "Menyu nomi", 100, 1)
            url = menu_url(string_field(data, "url", "Havola", 200, 1))
            position = menu_position(data.get("position", 0))
            result = connection.execute(
                "INSERT INTO menu(label, url, position, active) VALUES (?, ?, ?, ?)",
                (label, url, position, boolean_field(data, "active", True)),
            )
            action = "Menyu bandi qo‘shildi"
        elif path == "/api/programs":
            name = program_name(connection, string_field(data, "name", "Yo‘nalish nomi", 200, 1))
            description = string_field(data, "description", "Tavsif", 10_000)
            result = connection.execute(
                "INSERT INTO programs(name, description, active) VALUES (?, ?, ?)",
                (name, description, boolean_field(data, "active", True)),
            )
            action = "Yo‘nalish qo‘shildi"
        elif path == "/api/content":
            fields = content_fields(data)
            title = string_field(data, "title", "Sarlavha", 200, 1)
            body = string_field(data, "body", "Matn", 10_000, 1)
            result = connection.execute(
                "INSERT INTO content(kind, page, title, body, published, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (fields["kind"], fields["page"], title, body, boolean_field(data, "published"), now()),
            )
            action = "Material qo‘shildi"
        else:
            raise ApiError("API topilmadi.", 404)
        audit(connection, f"{action} #{result.lastrowid}")
        return result.lastrowid

    def upload_media(self, data):
        original_name = string_field(data, "name", "Fayl nomi", 200, 1)
        try:
            content = base64.b64decode(string_field(data, "data", "Rasm", 4_000_000, 1), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ApiError("Faylni o‘qib bo‘lmadi. 3 MB gacha rasm tanlang.") from exc
        if len(content) > 3_000_000:
            raise ApiError("Rasm hajmi 3 MB dan oshmasin.")
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            ext = ".png"
        elif content.startswith(b"\xff\xd8\xff"):
            ext = ".jpg"
        elif content.startswith(b"RIFF") and content[8:12] == b"WEBP":
            ext = ".webp"
        elif content.startswith((b"GIF87a", b"GIF89a")):
            ext = ".gif"
        else:
            raise ApiError("PNG, JPG, WEBP yoki GIF formatidagi rasmni tanlang.")
        file = UPLOAD / (uuid.uuid4().hex + ext)
        try:
            with connect() as connection:
                file.write_bytes(content)
                result = connection.execute(
                    "INSERT INTO media(filename, original_name, mime, size, created_at) VALUES (?, ?, ?, ?, ?)",
                    (file.name, original_name, MIME_TYPES[ext], len(content), now()),
                )
                audit(connection, "Rasm yuklandi")
        except (OSError, sqlite3.Error):
            file.unlink(missing_ok=True)
            raise
        self.send(201, {"id": result.lastrowid, "url": f"/media/{file.name}"})

    def patch(self, path):
        self.require(write=True)
        match = re.fullmatch(r"/api/(applications|content|programs|menu)/([0-9]{1,18})", path)
        if not match:
            raise ApiError("Yozuv topilmadi.", 404)
        table, item_id = match[1], int(match[2])
        data = self.payload()
        with connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            old = connection.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
            if not old:
                raise ApiError("Yozuv topilmadi.", 404)
            if table == "applications":
                status = data.get("status")
                if status not in STATUSES:
                    raise ApiError("Ariza holatini tanlang.")
                if status != old["status"]:
                    connection.execute(
                        "UPDATE applications SET status = ?, sync_version = sync_version + 1 WHERE id = ?",
                        (status, item_id),
                    )
                    audit(connection, f"Ariza #{item_id} holati yangilandi")
            else:
                fields = self.patch_fields(connection, table, item_id, data, dict(old))
                if not fields:
                    raise ApiError("O‘zgartiriladigan maydon berilmagan.")
                assignments = ", ".join(f"{key} = ?" for key in fields)
                connection.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", (*fields.values(), item_id))
                audit(connection, f"{table} #{item_id} yangilandi")
        if table == "applications":
            self.server.sheets.wake()
        self.send(200, {"ok": True})

    def patch_fields(self, connection, table, item_id, data, old):
        text_fields = {
            "programs": (("name", "Yo‘nalish nomi", 200, 1), ("description", "Tavsif", 10_000, 0)),
            "content": (("title", "Sarlavha", 200, 1), ("body", "Matn", 10_000, 1)),
            "menu": (("label", "Menyu nomi", 100, 1), ("url", "Havola", 200, 1)),
        }
        fields = {
            key: string_field(data, key, label, size, minimum)
            for key, label, size, minimum in text_fields[table] if key in data
        }
        flag = "published" if table == "content" else "active"
        if flag in data:
            fields[flag] = boolean_field(data, flag)
        if table == "programs" and "name" in fields and fields["name"] != old["name"]:
            program_name(connection, fields["name"], item_id)
        if table == "menu":
            if "url" in fields:
                fields["url"] = menu_url(fields["url"])
            if "position" in data:
                fields["position"] = menu_position(data["position"])
        if table == "content" and ("kind" in data or "page" in data):
            fields.update(content_fields(data, old))
        return fields

    def delete(self, path):
        self.require(write=True)
        match = re.fullmatch(r"/api/(content|programs|menu|media)/([0-9]{1,18})", path)
        if not match:
            raise ApiError("Yozuv topilmadi.", 404)
        table, item_id = match[1], int(match[2])
        with connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            file = None
            if table == "media":
                row = connection.execute("SELECT filename FROM media WHERE id = ?", (item_id,)).fetchone()
                if row:
                    file = UPLOAD / row["filename"]
            result = connection.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
            if not result.rowcount:
                raise ApiError("Yozuv topilmadi.", 404)
            audit(connection, f"{table} #{item_id} o‘chirildi")
        if file:
            try:
                file.unlink(missing_ok=True)
            except OSError:
                logging.warning("O‘chirilgan media faylini diskdan olib tashlab bo‘lmadi.")
        self.send(200, {"ok": True})


def main():
    parser = argparse.ArgumentParser(description="ISFT PRO mahalliy serveri")
    parser.add_argument("--open", action="store_true", help="Saytni brauzerda ochish")
    parser.add_argument("--configure-sheets", action="store_true", help="Google Sheets ulanishini sozlash")
    args = parser.parse_args()
    if args.configure_sheets:
        return configure_sheets(ROOT / "sheets.local.json")
    host = os.getenv("ISFT_HOST", "127.0.0.1")
    port = os.getenv("PORT", "8000")
    try:
        server = ThreadingHTTPServer((host, int(port)), Handler)
    except (OSError, ValueError, OverflowError) as exc:
        raise SystemExit(f"Server ochilmadi ({host}:{port}). Portni tekshiring. {exc}") from exc
    with server:
        init()
        server.sheets = SheetsSync(ROOT / "sheets.local.json", connect)
        server.sheets.start()
        address = f"http://{host}:{server.server_port}"
        print(f"Sayt: {address}/\nAdmin: {address}/admin.html\nTo‘xtatish: Ctrl+C", flush=True)
        if args.open:
            webbrowser.open(address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer to‘xtadi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
