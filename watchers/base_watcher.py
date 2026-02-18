"""
base_watcher.py — Shared base class for all Silver Tier watchers.
All watchers inherit from BaseWatcher and implement check_for_updates().
"""

import os
import logging
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class BaseWatcher:
    """
    Abstract base class for all watchers.

    Subclasses must implement:
        check_for_updates() -> list[dict]  — returns list of new items
        create_action_file(item: dict) -> Path  — writes to Needs_Action/
    """

    def __init__(self, vault_path: str | None = None, check_interval: int = 120):
        self.vault_path = Path(vault_path or os.getenv("VAULT_PATH", ".")).resolve()
        self.check_interval = check_interval
        self.needs_action = self.vault_path / "Needs_Action"
        self.done = self.vault_path / "Done"
        self.logs_dir = self.vault_path / "Logs"

        # Ensure key folders exist
        for folder in [self.needs_action, self.done, self.logs_dir]:
            folder.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(self.__class__.__name__)

    # ── Subclass interface ────────────────────────────────────────────────

    def check_for_updates(self) -> list[dict]:
        """Return a list of new items to process. Override in subclass."""
        raise NotImplementedError

    def create_action_file(self, item: dict) -> Path:
        """Write a Needs_Action file for the given item. Override in subclass."""
        raise NotImplementedError

    # ── Main loop ─────────────────────────────────────────────────────────

    def run(self):
        self.logger.info(f"Starting — vault: {self.vault_path}  interval: {self.check_interval}s")
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    path = self.create_action_file(item)
                    self.logger.info(f"Created action file: {path.name}")
                    self._append_log(item, path)
            except Exception as exc:
                self.logger.error(f"Watcher error: {exc}", exc_info=True)
            time.sleep(self.check_interval)

    # ── Logging helper ────────────────────────────────────────────────────

    def _append_log(self, item: dict, action_file: Path):
        import json

        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": self.__class__.__name__,
            "action_file": action_file.name,
            "item_summary": str(item)[:200],
        }
        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                entries = []
        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")
