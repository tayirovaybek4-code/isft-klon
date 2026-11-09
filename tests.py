"""Run with python tests.py. All writes use a temporary SQLite database."""

import base64
import http.cookiejar
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

import server
from sheets_sync import SheetsError, SheetsSync

PASSWORD = "TemporaryIntegrationPassword!89"
FORM = {
    "first_name": "Sinov", "last_name": "Abituriyent", "father_name": "Sinov o‘g‘li",
    "phone": "+998 (90) 123-45-67", "birth_date": "2005-01-23",
    "program_id": 1, "study_type": "Kunduzgi", "consent": True, "request_id": "f" * 32,
}


class ProjectTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        locations = patch.multiple(server, DB=self.root / "isft.db", UPLOAD=self.root / "uploads")
        locations.start()
        self.addCleanup(locations.stop)
        with patch.dict(os.environ, {"ADMIN_PASSWORD": PASSWORD, "ISFT_HTTPS": "0"}):
            server.init()
        httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        httpd.sheets = SheetsSync(self.root / "sheets.local.json", server.connect)
        self.httpd = httpd
        self.base = f"http://127.0.0.1:{httpd.server_port}"
        self.opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf = ""
        thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        thread.start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(thread.join, 3)
        self.addCleanup(httpd.shutdown)

    def request(self, path, method="GET", data=None):
        body = json.dumps(data).encode() if data is not None else None
        request = Request(self.base + path, data=body, method=method, headers={
            "Content-Type": "application/json", "X-CSRF-Token": self.csrf,
        })
        try:
            response = self.opener.open(request, timeout=4)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.loads(response.read())

    def login(self):
        self.assertEqual(self.request("/api/login", "POST", {"username": "admin", "password": "wrong"})[0], 401)
        self.assertEqual(self.request("/api/login", "POST", {"username": "admin", "password": PASSWORD})[0], 200)
        session = self.request("/api/session")[1]
        self.assertTrue(session["logged_in"])
        self.csrf = session["csrf"]

    def test_application_can_be_retried_concurrently(self):
        def submit(_):
            return self.request("/api/apply", "POST", FORM)
        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(submit, range(4)))
        self.assertEqual(sorted(code for code, _ in responses), [200, 200, 200, 201])
        self.assertEqual({data["application_id"] for _, data in responses}, {1})
        self.assertEqual(self.request("/api/apply", "POST", {**FORM, "consent": False})[0], 400)
        self.assertEqual(self.request("/api/apply", "POST", {**FORM, "phone": "---------", "request_id": "e" * 32})[0], 400)
        self.assertEqual(self.request("/api/apply", "POST", [FORM])[0], 400)
        self.assertEqual(self.request("/api/applications")[0], 401)
        self.login()
        applications = self.request("/api/applications")[1]
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0]["father_name"], FORM["father_name"])
        self.assertEqual(applications[0]["consent"], 1)
        self.assertNotIn("submission_key", applications[0])
        self.assertEqual(self.request("/api/applications/1", "PATCH", {"status": "Qabul qilingan"})[0], 200)
        dashboard = self.request("/api/dashboard")[1]
        self.assertEqual(dashboard["statuses"]["Qabul qilingan"], 1)
        self.assertEqual(dashboard["today"], 1)
        self.assertEqual(len(dashboard["days"]), 30)

    def test_program_and_public_content_management(self):
        programs = self.request("/api/public/programs")[1]
        self.assertEqual(len(programs), 16)
        self.assertEqual(len(self.request("/api/public/menu")[1]), 6)
        legacy_form = {key: value for key, value in FORM.items() if key not in ("request_id", "consent", "program_id")}
        legacy_form["program"] = programs[0]["name"]
        self.assertEqual(self.request("/api/apply", "POST", legacy_form)[0], 201)
        self.login()

        status, hidden = self.request("/api/programs", "POST", {"name": "Yashirin yo‘nalish", "active": False})
        self.assertEqual(status, 201)
        self.assertNotIn(hidden["id"], {item["id"] for item in self.request("/api/public/programs")[1]})
        self.assertEqual(self.request("/api/programs/1", "PATCH", {"name": "Dasturiy injiniring"})[0], 200)
        self.assertEqual(self.request("/api/dashboard")[1]["ranks"][0]["name"], "Dasturiy injiniring")
        self.assertEqual(self.request("/api/programs/1", "DELETE")[0], 200)
        self.assertEqual(self.request("/api/applications")[1][0]["program"], legacy_form["program"])
        self.assertEqual(self.request("/api/dashboard")[1]["ranks"][0]["archived"], 1)

        status, item = self.request("/api/content", "POST", {
            "kind": "Sahifa", "page": "about", "title": "Sinov sarlavha", "body": "Sinov matn", "published": True,
        })
        self.assertEqual(status, 201)
        self.assertEqual(self.request("/api/public/content")[1][0]["page"], "about")
        self.assertEqual(self.request(f"/api/content/{item['id']}", "PATCH", {"kind": "Yangilik"})[0], 200)
        self.assertEqual(self.request("/api/public/content")[1][0]["kind"], "Yangilik")
        self.assertEqual(self.request("/api/settings", "POST", {"hero_title": "Sinov bosh sahifa"})[0], 200)
        self.assertEqual(self.request("/api/public/settings")[1]["hero_title"], "Sinov bosh sahifa")
        self.assertEqual(self.request("/api/menu", "POST", {"label": "Xato", "url": "/about.html", "position": "a"})[0], 400)
        self.assertEqual(self.request("/api/menu", "POST", {"label": "Sinov", "url": "/about.html"})[0], 201)

    def test_media_and_logout_require_admin(self):
        self.login()
        csrf, self.csrf = self.csrf, ""
        self.assertEqual(self.request("/api/settings", "POST", {"hero_title": "Sinov"})[0], 403)
        self.csrf = csrf
        png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jP+kAAAAASUVORK5CYII="
        status, image = self.request("/api/media", "POST", {"name": "sinov.png", "data": png})
        self.assertEqual(status, 201)
        with self.opener.open(self.base + image["url"], timeout=4) as response:
            self.assertEqual(response.headers.get_content_type(), "image/png")
            self.assertEqual(response.read(), base64.b64decode(png))
        self.assertEqual(self.request(f"/api/media/{image['id']}", "DELETE")[0], 200)
        self.assertEqual(self.request(image["url"])[0], 404)
        self.assertEqual(self.request("/api/logout", "POST", {})[0], 200)
        self.assertEqual(self.request("/api/sheets")[0], 401)

    def test_google_failure_and_status_change_stay_pending(self):
        self.request("/api/apply", "POST", FORM)
        self.login()
        self.assertEqual(self.request("/api/sheets")[1]["pending"], 1)
        config = self.root / "sheets.local.json"
        config.write_text(json.dumps({
            "url": "https://script.google.com/macros/s/FakeDeploy/exec",
            "secret": "a" * 32, "sheet_id": "test_sheet_identifier_1",
        }))
        sync = SheetsSync(config, server.connect)
        with patch("sheets_sync.send_to_google", side_effect=SheetsError("Sinov uzilishi")):
            with self.assertRaises(SheetsError):
                sync.sync_once()
        self.assertEqual(sync.status()["pending"], 1)

        def edit_during_upload(url, secret, sheet_id, rows):
            self.assertEqual(rows[0]["phone"], FORM["phone"])
            self.assertEqual(rows[0]["sync_version"], 1)
            self.assertEqual(self.request("/api/applications/1", "PATCH", {"status": "Qabul qilingan"})[0], 200)

        with patch("sheets_sync.send_to_google", side_effect=edit_during_upload):
            self.assertTrue(sync.sync_once())
        self.assertEqual(sync.status()["pending"], 1)

        # A new worker after a restart still sees the latest pending row.
        sync = SheetsSync(config, server.connect)
        with patch("sheets_sync.send_to_google") as delivery:
            self.assertTrue(sync.sync_once())
            delivered = delivery.call_args.args[-1][0]
            self.assertEqual(delivered["submission_key"], FORM["request_id"])
            self.assertEqual(delivered["status"], "Qabul qilingan")
            self.assertEqual(delivered["sync_version"], 2)
        self.assertEqual(sync.status()["pending"], 0)
        self.assertEqual(sync.status()["synced"], 1)


class MigrationTests(unittest.TestCase):
    def test_existing_arizalar_and_admin_password_survive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db = root / "isft.db"
            with sqlite3.connect(db) as connection:
                connection.executescript("""
                    CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, salt TEXT, digest TEXT);
                    INSERT INTO users VALUES (1, 'admin', 'old-salt', 'old-digest');
                    CREATE TABLE programs (id INTEGER PRIMARY KEY, name TEXT, description TEXT, active INTEGER);
                    INSERT INTO programs VALUES (9, 'Marketing', '', 1);
                    CREATE TABLE applications (
                        id INTEGER PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
                        father_name TEXT, phone TEXT NOT NULL, birth_date TEXT, program TEXT NOT NULL,
                        study_type TEXT, status TEXT DEFAULT 'Yangi', created_at TEXT NOT NULL
                    );
                    INSERT INTO applications(id, first_name, last_name, phone, program, created_at)
                    VALUES (81, 'Old', 'Test', '+998901234567', 'Marketing', '2025-03-03T08:00:00');
                """)
            with patch.multiple(server, DB=db, UPLOAD=root / "uploads"):
                server.init()
                server.init()
                with server.connect() as connection:
                    row = connection.execute("SELECT * FROM applications WHERE id = 81").fetchone()
                    self.assertEqual(row["program_id"], 9)
                    self.assertEqual(row["first_name"], "Old")
                    self.assertIsNone(row["consent"])
                    self.assertRegex(row["submission_key"], r"^[a-f0-9]{32}$")
                    self.assertEqual(connection.execute("SELECT digest FROM users").fetchone()[0], "old-digest")


if __name__ == "__main__":
    unittest.main(verbosity=2)
