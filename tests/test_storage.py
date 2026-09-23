"""Storage and HTTP integration checks for the local vault service."""

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import Vault, load_settings, make_handler
from http.server import ThreadingHTTPServer


class VaultServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.config = root / "config.json"
        self.config.write_text(json.dumps({
            "server": {"host": "127.0.0.1", "port": 0},
            "storage": {"directory": "./data", "vault_filename": "main.json",
                        "backup_directory": "./backups", "keep_backups": 2},
            "autosave": {"debounce_ms": 200},
        }), encoding="utf-8")
        self.settings = load_settings(self.config)
        self.vault = Vault(self.settings)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.vault, self.settings))
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def request(self, method, path, data=None, headers=None):
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = Request(self.url + path, data=body, method=method,
                      headers={"Content-Type": "application/json", **(headers or {})})
        try:
            with urlopen(req, timeout=3) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)

    def test_seed_save_backup_reopen_and_conflict(self):
        status, first = self.request("GET", "/api/vault")
        self.assertEqual(status, 200)
        self.assertEqual(len(first["vault"]["links"]), 3)
        original = self.settings["vault"].read_bytes()
        self.assertEqual(first["revision"], self.vault.read()[1])

        changed = first["vault"]
        changed["links"][0]["favorite"] = not changed["links"][0]["favorite"]
        changed["updatedAt"] = "2026-09-23T00:00:00Z"
        status, saved = self.request("POST", "/api/vault", {"revision": first["revision"], "vault": changed})
        self.assertEqual(status, 200)
        self.assertTrue(saved["saved"])
        self.assertNotEqual(saved["revision"], first["revision"])
        backups = list(self.settings["backup_dir"].glob("*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)

        status, rejected = self.request("POST", "/api/vault", {"revision": first["revision"], "vault": first["vault"]})
        self.assertEqual(status, 409)
        self.assertEqual(rejected["revision"], saved["revision"])
        reopened, revision = Vault(self.settings).read()
        self.assertEqual(revision, saved["revision"])
        self.assertEqual(reopened["links"][0]["favorite"], changed["links"][0]["favorite"])

    def test_invalid_data_does_not_replace_vault(self):
        _, first = self.request("GET", "/api/vault")
        status, _ = self.request("POST", "/api/vault", {"revision": first["revision"], "vault": {"links": []}})
        self.assertEqual(status, 400)
        self.assertEqual(first["revision"], self.vault.read()[1])
        self.assertFalse(self.settings["backup_dir"].exists())

    def test_backup_retention(self):
        _, current = self.request("GET", "/api/vault")
        for number in range(4):
            data = current["vault"]
            data["updatedAt"] = f"2026-09-23T00:00:0{number}Z"
            status, saved = self.request("POST", "/api/vault", {"revision": current["revision"], "vault": data})
            self.assertEqual(status, 200)
            current = {"revision": saved["revision"], "vault": data}
        self.assertEqual(len(list(self.settings["backup_dir"].glob("*.json"))), 2)

    def test_rejects_cross_origin_write(self):
        _, first = self.request("GET", "/api/vault")
        status, _ = self.request("POST", "/api/vault", {"revision": first["revision"], "vault": first["vault"]},
                                 {"Origin": "https://unrelated.example"})
        self.assertEqual(status, 403)

    def test_config_paths_resolve_from_config_file(self):
        self.assertEqual(self.settings["vault"], Path(self.temp.name) / "data" / "main.json")
        self.assertEqual(self.settings["backup_dir"], Path(self.temp.name) / "backups")


if __name__ == "__main__":
    unittest.main()
