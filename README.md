# Utah Command Center v9 — local vault edition

This repository contains the dashboard, a **public three-link sample vault**, a local Python service, and a storage configuration. The service automatically loads and saves your vault on your computer. There are no third-party Python dependencies or cloud storage requirements. The real personal vault is deliberately excluded from this public repository.

## Start on Windows

1. Extract the entire ZIP into a folder where your account can write files. Keep `app.py`, `index.html`, `config.json`, and `initial_vault.json` together.
2. Install Python 3.10 or later if needed.
3. Double-click **`start_windows.bat`**. Keep the command window open while using the dashboard.
4. The browser should open `http://127.0.0.1:8765/`. If it does not, paste that address into your browser yourself.
5. Confirm the page says **Saved on disk** and shows **3 links** for a new installation. If you see **Local vault offline**, check the command window and use the address it prints.

On macOS or Linux, run `sh start_mac_linux.sh` in a terminal. You can also run `python app.py` from the extracted folder on Windows, or `python3 app.py` elsewhere.

Do **not** open `index.html` directly for normal use. The local service supplies automatic disk storage.

## Choose where files are stored

Copy `config.json` to **`config.local.json`**, then edit the copy **while the service is stopped**. The launchers automatically use `config.local.json` when it exists. The local configuration is ignored by Git. Its `storage.directory` points to the folder holding the current vault, and `storage.backup_directory` points to the rolling backup folder. Relative paths are resolved from the location of the selected config file; absolute paths are also allowed.

Example for a Windows folder:

```json
{
  "server": {"host": "127.0.0.1", "port": 8765},
  "storage": {
    "directory": "C:/Users/YOUR_USERNAME/Documents/UtahCommandCenter/vault",
    "vault_filename": "utah_command_center_vault.json",
    "backup_directory": "C:/Users/YOUR_USERNAME/Documents/UtahCommandCenter/backups",
    "keep_backups": 30
  },
  "autosave": {"debounce_ms": 900}
}
```

Use forward slashes as shown, or escape every backslash in JSON. On first startup at a new location, the service **copies the sample `initial_vault.json`** into `storage.directory` as `storage.vault_filename`. It never intentionally replaces an existing vault during startup. If you change the directory later and want your edits to follow, move your current vault file to the new directory before restarting.

To use an existing personal vault, copy your JSON to the configured vault filename **before the first launch**, or launch the app and choose **Replace from JSON**. The latter writes a backup of the existing vault before saving the imported data. Keep personal vaults out of the repository; `vault-data/`, `vault-backups/`, and `config.local.json` are ignored by Git.

The default locations are `./vault-data/utah_command_center_vault.json` and `./vault-backups/`, both relative to `config.json`. Changing `keep_backups` to 0 disables automatic backups. The service creates a backup of the previous version before each changed save and keeps the latest configured number.

## Normal use

- Edit a link, category, or dashboard as usual. The page saves changes to disk after a 900 ms pause by default. **Save now** and Ctrl+S write immediately.
- **Download backup** makes a browser download. **Download vault** exports the current JSON. Neither changes the configured storage folder.
- **Replace from JSON** loads a selected JSON file and saves its contents to the configured vault. **Import JSON/CSV** merges records instead.
- **Reload disk** reads the configured vault again. If you have unsaved changes, it offers to download a backup before replacing the view.
- If another tab or external program changes the vault, the page stops saving and displays **Save conflict**. Download a backup of your edits, then reload the disk version. This prevents an unseen overwrite.
- If a save is interrupted, the page retains a browser cache. On a later visit, it may offer **Recover cached edits** when that cache is newer than the disk vault.

The repository includes only sample data. The updated Open action trims leading whitespace and identifies local path bookmarks so they do not open a misleading web address. The old `utah_work_dashboard_v6_sheet_import.html` and CSV template are retained as legacy references.

## Configuration and recovery

The service listens only on the local machine (`127.0.0.1` or `localhost`). If port 8765 is already occupied, change `server.port` and restart; use the address printed in the command window. Do not put passwords or API keys in the vault: it is plain JSON on your disk. Back up the vault folder and backup folder with your normal computer backup system.

If the dashboard cannot load, check that `config.json` remains valid JSON and that the configured folders are writable. To restore a backup, stop the service, copy the desired file from the backup folder to the configured vault filename, then start the service again. Keep an extra copy of the current vault before restoring.

## Files

| File | Purpose |
| --- | --- |
| `config.json` | Local address, vault/backup locations, retention, autosave delay |
| `app.py` | Serves the page and performs validated, atomic, revision-checked saves |
| `index.html` | Dashboard interface and automatic load/save client |
| `initial_vault.json` | Public sample data used only when no saved vault exists |
| `config.local.json` | Optional personal settings file, created by you and ignored by Git |
| `start_windows.bat`, `start_mac_linux.sh` | Launchers |
| `ROADMAP.md` | Additional improvements to consider |

To run storage tests from the package folder: `python -m unittest discover -s tests -v`. If Node.js is installed, `node tests/client_smoke.js` also checks initial loading and autosave logic without a browser.
