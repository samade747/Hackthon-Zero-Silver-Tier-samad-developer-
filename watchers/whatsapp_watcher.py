"""
whatsapp_watcher.py — Playwright-based WhatsApp Web monitor.

First-time setup:
    python watchers/whatsapp_watcher.py --setup
    (Opens browser, scan QR code, then press Enter)

Normal operation (headless):
    python watchers/whatsapp_watcher.py
    (Or via PM2 — see ecosystem.config.js)
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add watchers dir to path so base_watcher imports cleanly
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher

load_dotenv()

URGENT_KEYWORDS = [
    "urgent", "asap", "invoice", "payment",
    "help", "problem", "error", "deadline", "critical",
    "emergency", "immediately", "overdue",
]


class WhatsAppWatcher(BaseWatcher):
    def __init__(self, vault_path=None):
        super().__init__(vault_path, check_interval=30)
        self.session_path = os.getenv("WHATSAPP_SESSION_PATH", "./whatsapp_session")
        self.seen_messages = self._load_seen()

    # ── Seen cache ────────────────────────────────────────────────────────

    def _load_seen(self) -> set:
        cache = self.vault_path / ".whatsapp_seen.txt"
        return (
            set(cache.read_text(encoding="utf-8").strip().splitlines())
            if cache.exists()
            else set()
        )

    def _save_seen(self):
        (self.vault_path / ".whatsapp_seen.txt").write_text(
            "\n".join(self.seen_messages), encoding="utf-8"
        )

    # ── QR setup (run once) ───────────────────────────────────────────────

    @staticmethod
    def setup_session(session_path: str):
        """Open a real browser window so the user can scan the QR code."""
        from playwright.sync_api import sync_playwright

        print(f"\nOpening WhatsApp Web — scan the QR code, then press Enter here.\n")
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                session_path,
                headless=False,
                args=["--no-sandbox"],
            )
            page = ctx.new_page()
            page.goto("https://web.whatsapp.com")
            input(">>> Scan QR code in the browser window, then press Enter: ")
            ctx.close()
        print(f"\nSession saved to: {session_path}")
        print("You can now run the watcher normally (headless).\n")

    # ── Core ──────────────────────────────────────────────────────────────

    def check_for_updates(self) -> list[dict]:
        messages = []
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                ctx = p.chromium.launch_persistent_context(
                    self.session_path,
                    headless=True,
                    args=["--no-sandbox"],
                )
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                page.goto("https://web.whatsapp.com", timeout=30_000)
                page.wait_for_timeout(5_000)

                for chat in page.query_selector_all('[data-testid="cell-frame-container"]'):
                    badge = chat.query_selector('[data-testid="icon-unread-count"]')
                    if not badge:
                        continue

                    name_el = chat.query_selector('[data-testid="cell-frame-title"]')
                    prev_el = chat.query_selector(
                        '[data-testid="last-msg-status"] + span, '
                        '.copyable-text span'
                    )
                    name = name_el.inner_text().strip() if name_el else "Unknown"
                    preview = prev_el.inner_text().strip() if prev_el else ""

                    msg_id = f"{name}_{preview[:30]}"
                    if msg_id in self.seen_messages:
                        continue

                    is_urgent = any(kw in preview.lower() for kw in URGENT_KEYWORDS)
                    messages.append(
                        {
                            "id": msg_id,
                            "sender": name,
                            "preview": preview,
                            "urgent": is_urgent,
                        }
                    )
                    self.seen_messages.add(msg_id)

                ctx.close()

        except Exception as exc:
            self.logger.error(f"WhatsApp error: {exc}")

        self._save_seen()
        return messages

    def create_action_file(self, msg: dict) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        priority = "urgent" if msg["urgent"] else "normal"
        safe_sender = "".join(c if c.isalnum() else "_" for c in msg["sender"])[:20]

        content = f"""---
type: whatsapp
sender: {msg['sender']}
priority: {priority}
received: {datetime.now().isoformat()}
status: pending
---

## WhatsApp Message

**From:** {msg['sender']}
**Message preview:** {msg['preview']}
**Urgent:** {'YES ⚠️' if msg['urgent'] else 'No'}

## Suggested Actions

- [ ] Draft reply using `skills/whatsapp/SKILL.md`
- [ ] Validate any financial figures against `Accounting/Rates.md`
- [ ] Create approval file in `/Pending_Approval/` before replying
"""
        path = self.needs_action / f"WHATSAPP_{priority.upper()}_{ts}_{safe_sender}.md"
        path.write_text(content, encoding="utf-8")
        return path


if __name__ == "__main__":
    if "--setup" in sys.argv:
        session = os.getenv("WHATSAPP_SESSION_PATH", "./whatsapp_session")
        WhatsAppWatcher.setup_session(session)
    else:
        WhatsAppWatcher().run()
