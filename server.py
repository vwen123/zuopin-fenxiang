#!/usr/bin/env python3
"""
作品分享区 — 本地管理服务器
用法：python3 server.py
然后在浏览器开启 http://localhost:8080
"""

import http.server
import json
import os
import cgi
import mimetypes
import urllib.parse

PORT = 8080
DATA_FILE = "data.json"
UPLOADS_DIR = "uploads"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cards": []}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Handler(http.server.BaseHTTPRequestHandler):

    # ── CORS & common headers ──────────────────────────────────────────────
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    # ── OPTIONS preflight ─────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    # ── GET — static files ────────────────────────────────────────────────
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            path = "/index.html"

        file_path = path.lstrip("/")
        if os.path.isfile(file_path):
            mime = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self._cors()
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    # ── POST /api/card — add card ─────────────────────────────────────────
    def do_POST(self):
        if self.path != "/api/card":
            self.send_response(404)
            self.end_headers()
            return

        content_type = self.headers.get("Content-Type", "")
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type},
        )

        card_type = form.getvalue("type", "")
        card_id = int(form.getvalue("id", "0"))

        os.makedirs(UPLOADS_DIR, exist_ok=True)
        card = {"id": card_id, "type": card_type}

        if card_type == "image":
            item = form["file"]
            fname = f"{card_id}_{item.filename}"
            fpath = os.path.join(UPLOADS_DIR, fname)
            with open(fpath, "wb") as f:
                f.write(item.file.read())
            card["src"] = f"{UPLOADS_DIR}/{fname}"
            card["caption"] = form.getvalue("caption", "")

        elif card_type == "pdf":
            item = form["file"]
            fname = f"{card_id}_{item.filename}"
            fpath = os.path.join(UPLOADS_DIR, fname)
            with open(fpath, "wb") as f:
                f.write(item.file.read())
            card["src"] = f"{UPLOADS_DIR}/{fname}"
            card["name"] = item.filename
            card["title"] = (
                form.getvalue("title", "")
                or item.filename.replace(".pdf", "").replace(".PDF", "")
            )
            card["desc"] = form.getvalue("desc", "")

        elif card_type == "link":
            card["url"] = form.getvalue("url", "")
            card["title"] = form.getvalue("title", "")
            card["desc"] = form.getvalue("desc", "")

        else:
            self._json(400, {"ok": False, "error": "unknown type"})
            return

        data = load_data()
        data["cards"].append(card)
        save_data(data)
        self._json(200, {"ok": True, "card": card})

    # ── DELETE /api/card/<id> — remove card ───────────────────────────────
    def do_DELETE(self):
        if not self.path.startswith("/api/card/"):
            self.send_response(404)
            self.end_headers()
            return

        try:
            card_id = int(self.path.split("/")[-1])
        except ValueError:
            self._json(400, {"ok": False, "error": "invalid id"})
            return

        data = load_data()
        for card in data["cards"]:
            if card["id"] == card_id:
                src = card.get("src", "")
                if src.startswith("uploads/") and os.path.isfile(src):
                    try:
                        os.remove(src)
                    except OSError:
                        pass
                break

        data["cards"] = [c for c in data["cards"] if c["id"] != card_id]
        save_data(data)
        self._json(200, {"ok": True})

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} — {fmt % args}")


if __name__ == "__main__":
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        save_data({"cards": []})

    print("=" * 50)
    print("  ✨ 作品分享区管理服务器已启动")
    print(f"  请在浏览器开启：http://localhost:{PORT}")
    print("  按 Ctrl+C 停止")
    print("=" * 50)

    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
