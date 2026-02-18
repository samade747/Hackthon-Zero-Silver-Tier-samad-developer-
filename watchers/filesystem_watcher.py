"""
filesystem_watcher.py — Watches the /Drop/ folder for new files.
When a file appears, it creates a Needs_Action file and moves the
original into /Needs_Action/ for Claude to process.

This is the simplest watcher — no external APIs required.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FilesystemWatcher] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

VAULT_PATH = Path(os.getenv("VAULT_PATH", ".")).resolve()
DROP_FOLDER = VAULT_PATH / "Drop"
NEEDS_ACTION = VAULT_PATH / "Needs_Action"
LOGS_DIR = VAULT_PATH / "Logs"


class DropFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        src = Path(event.src_path)
        # Skip hidden files and temp files
        if src.name.startswith(".") or src.suffix in {".tmp", ".part"}:
            return

        import time
        time.sleep(0.5)  # Wait for file to finish writing

        logging.info(f"New file dropped: {src.name}")
        self._process_file(src)

    def _process_file(self, src: Path):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in src.name)

        # Move original into Needs_Action
        dest = NEEDS_ACTION / src.name
        try:
            shutil.move(str(src), str(dest))
        except Exception as exc:
            logging.error(f"Could not move {src.name}: {exc}")
            return

        # Create action file
        action_file = NEEDS_ACTION / f"FILE_{ts}_{safe_name}.md"
        content = f"""---
type: file_drop
filename: {src.name}
file_path: {dest}
received: {datetime.now().isoformat()}
status: pending
---

## File Received

**Filename:** `{src.name}`
**Dropped at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Moved to:** `Needs_Action/{src.name}`

## Suggested Actions

- [ ] Inspect the file content
- [ ] Determine action required (invoice, contract, report, etc.)
- [ ] Route using `skills/task-router/SKILL.md`
- [ ] Create approval file if external action is needed
"""
        action_file.write_text(content, encoding="utf-8")
        logging.info(f"Created action file: {action_file.name}")
        _append_log(src.name, action_file.name)


def _append_log(filename: str, action_file: str):
    import json
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "FilesystemWatcher",
        "dropped_file": filename,
        "action_file": action_file,
    }
    entries = []
    if log_file.exists():
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    entries.append(entry)
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def run():
    DROP_FOLDER.mkdir(parents=True, exist_ok=True)
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    observer = Observer()
    observer.schedule(DropFolderHandler(), str(DROP_FOLDER), recursive=False)
    observer.start()
    logging.info(f"Watching drop folder: {DROP_FOLDER}")

    try:
        import time
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    run()
