"""Utah Command Center local vault service.

Serves the dashboard on loopback, loads the configured JSON vault, and saves
updates atomically with backups and revision checks. Requires Python 3.10+;
no third-party packages or network accounts are required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
MAX_BODY_BYTES = 8 * 1024 * 1024


def load_settings(config_path: Path) -> dict:
    config_path = config_path.resolve()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    storage = data["storage"]

    def location(value: str) -> Path:
        path = Path(value).expanduser()
        return (path if path.is_absolute() else config_path.parent / path).resolve()

    filename = storage["vault_filename"]
    if Path(filename).name != filename or not filename.lower().endswith(".json"):
        raise ValueError("storage.vault_filename must be a plain .json filename")
    host = data["server"].get("host", "127.0.0.1")
    if host not in ("127.0.0.1", "localhost"):
        raise ValueError("Only localhost / 127.0.0.1 is supported")
    port = int(data["server"].get("port", 8765))
    if not 0 <= port <= 65535:
        raise ValueError("server.port must be between 0 and 65535")
    keep = int(storage.get("keep_backups", 30))
    if not 0 <= keep <= 10000:
        raise ValueError("storage.keep_backups must be between 0 and 10000")
    debounce = int(data.get("autosave", {}).get("debounce_ms", 900))
    if not 100 <= debounce <= 60000:
        raise ValueError("autosave.debounce_ms must be between 100 and 60000")
    return {
        "host": host, "port": port,
        "vault": location(storage["directory"]) / filename,
        "backup_dir": location(storage["backup_directory"]),
        "keep_backups": keep, "debounce_ms": debounce,
    }


def atomic_write(path: Path, contents: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".vault-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def revision(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


class Vault:
    def __init__(self, settings: dict, seed: Path = ROOT / "initial_vault.json"):
        self.settings = settings
        self.path = settings["vault"]
        self.lock = threading.RLock()
        if not self.path.exists():
            initial = seed.read_bytes()
            self.validate(initial)
            atomic_write(self.path, initial)

    @staticmethod
    def validate(contents: bytes) -> dict:
        data = json.loads(contents)
        if not isinstance(data, dict) or any(not isinstance(data.get(k), list)
                                              for k in ("dashboards", "categories", "links")):
            raise ValueError("Vault must contain dashboards, categories, and links arrays")
        for key in ("dashboards", "categories", "links"):
            if not all(isinstance(record, dict) for record in data[key]):
                raise ValueError(f"Every {key} record must be an object")
        return data

    def read(self) -> tuple[dict, str]:
        with self.lock:
            contents = self.path.read_bytes()
            return self.validate(contents), revision(contents)

    def save(self, data: dict, expected_revision: str) -> tuple[str, bool]:
        with self.lock:
            previous = self.path.read_bytes()
            current = revision(previous)
            if current != expected_revision:
                raise RevisionConflict(current)
            contents = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            self.validate(contents)
            if contents == previous:
                return current, False
            self._backup(previous)
            atomic_write(self.path, contents)
            return revision(contents), True

    def _backup(self, contents: bytes) -> None:
        keep = self.settings["keep_backups"]
        if not keep:
            return
        directory = self.settings["backup_dir"]
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        name = f"{self.path.stem}.{stamp}.{revision(contents)[:8]}.json"
        atomic_write(directory / name, contents)
        backups = sorted(directory.glob(f"{self.path.stem}.*.json"))
        for old in backups[:-keep]:
            old.unlink()


class RevisionConflict(Exception):
    def __init__(self, current: str):
        self.current = current


def make_handler(vault: Vault, settings: dict):
    class Handler(BaseHTTPRequestHandler):
        server_version = "UtahCommandCenter/9"

        def _host_ok(self) -> bool:
            try:
                host = urlsplit("http://" + self.headers.get("Host", "")).hostname
                return host in ("127.0.0.1", "localhost")
            except ValueError:
                return False

        def _origin_ok(self) -> bool:
            origin = self.headers.get("Origin")
            if not origin:
                return True
            parsed = urlsplit(origin)
            return (parsed.scheme == "http"
                    and parsed.hostname in ("127.0.0.1", "localhost")
                    and parsed.port == self.server.server_port)

        def _send(self, status: int, content: bytes, mime: str):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(content)

        def _json(self, status: int, data: dict):
            self._send(status, json.dumps(data).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self):
            if not self._host_ok():
                return self._json(403, {"error": "Invalid host"})
            route = urlsplit(self.path).path
            if route in ("/", "/index.html"):
                return self._send(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
            if route == "/api/config":
                return self._json(200, {"vault_path": str(vault.path), "backup_path": str(settings["backup_dir"]),
                                        "debounce_ms": settings["debounce_ms"]})
            if route == "/api/vault":
                try:
                    data, rev = vault.read()
                    return self._json(200, {"vault": data, "revision": rev})
                except (OSError, ValueError, json.JSONDecodeError) as exc:
                    return self._json(500, {"error": f"Cannot read vault: {exc}"})
            return self._json(404, {"error": "Not found"})

        def do_POST(self):
            if not self._host_ok() or not self._origin_ok():
                return self._json(403, {"error": "Invalid host or origin"})
            if urlsplit(self.path).path != "/api/vault":
                return self._json(404, {"error": "Not found"})
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                return self._json(415, {"error": "Expected application/json"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > MAX_BODY_BYTES:
                    return self._json(413, {"error": "Invalid or oversized payload"})
                request = json.loads(self.rfile.read(size))
                if not isinstance(request, dict) or not isinstance(request.get("revision"), str):
                    return self._json(400, {"error": "Revision is required"})
                rev, wrote = vault.save(request["vault"], request["revision"])
                return self._json(200, {"revision": rev, "saved": wrote})
            except RevisionConflict as exc:
                return self._json(409, {"error": "Vault changed on disk or in another tab", "revision": exc.current})
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                return self._json(400, {"error": str(exc)})
            except OSError as exc:
                return self._json(500, {"error": f"Cannot save vault: {exc}"})

        def log_message(self, fmt, *args):
            # Keep request bodies and vault link contents out of server logs.
            print(f"[{datetime.now(timezone.utc).isoformat()}] {self.address_string()} {fmt % args}")

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Utah Command Center local vault")
    parser.add_argument("--config", type=Path, default=ROOT / "config.json", help="Configuration JSON path")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the web browser")
    args = parser.parse_args()
    settings = load_settings(args.config)
    vault = Vault(settings)
    with ThreadingHTTPServer((settings["host"], settings["port"]), make_handler(vault, settings)) as server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"Dashboard: {url}\nVault: {vault.path}\nBackups: {settings['backup_dir']}", flush=True)
        if not args.no_browser:
            threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
