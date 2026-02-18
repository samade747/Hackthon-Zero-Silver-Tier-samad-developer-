"""
gmail_watcher.py — Monitors Gmail for important/unread emails every 2 minutes.
Creates a Needs_Action file for each new email that matches the filter.

Prerequisites:
    1. Gmail OAuth credentials set up (gmail_credentials.json + gmail_token.json)
    2. GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH set in .env
"""

import os
import json
from pathlib import Path
from datetime import datetime
from base_watcher import BaseWatcher

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

SEEN_CACHE_FILE = ".gmail_seen.txt"


class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path=None):
        super().__init__(vault_path, check_interval=120)  # every 2 min
        self.creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./gmail_credentials.json")
        self.token_path = os.getenv("GMAIL_TOKEN_PATH", "./gmail_token.json")
        self.seen_ids = self._load_seen()

    # ── Auth ──────────────────────────────────────────────────────────────

    def _get_service(self):
        creds = None
        if Path(self.token_path).exists():
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            Path(self.token_path).write_text(creds.to_json(), encoding="utf-8")
        return build("gmail", "v1", credentials=creds)

    # ── Seen cache ────────────────────────────────────────────────────────

    def _load_seen(self) -> set:
        cache = self.vault_path / SEEN_CACHE_FILE
        return set(cache.read_text(encoding="utf-8").strip().splitlines()) if cache.exists() else set()

    def _save_seen(self):
        (self.vault_path / SEEN_CACHE_FILE).write_text(
            "\n".join(self.seen_ids), encoding="utf-8"
        )

    # ── Core ──────────────────────────────────────────────────────────────

    def check_for_updates(self) -> list[dict]:
        emails = []
        try:
            service = self._get_service()
            # Fetch unread messages in INBOX (or marked important)
            result = service.users().messages().list(
                userId="me",
                q="is:unread is:inbox",
                maxResults=20,
            ).execute()

            messages = result.get("messages", [])
            for msg_meta in messages:
                msg_id = msg_meta["id"]
                if msg_id in self.seen_ids:
                    continue

                msg = service.users().messages().get(
                    userId="me", id=msg_id, format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()

                headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                snippet = msg.get("snippet", "")
                labels = msg.get("labelIds", [])

                emails.append({
                    "id": msg_id,
                    "from": headers.get("From", "Unknown"),
                    "subject": headers.get("Subject", "(no subject)"),
                    "date": headers.get("Date", ""),
                    "snippet": snippet[:300],
                    "important": "IMPORTANT" in labels,
                })
                self.seen_ids.add(msg_id)

        except Exception as exc:
            self.logger.error(f"Gmail fetch error: {exc}")

        self._save_seen()
        return emails

    def create_action_file(self, email: dict) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        priority = "urgent" if email.get("important") else "normal"
        safe_subject = "".join(c if c.isalnum() else "_" for c in email["subject"])[:40]

        content = f"""---
type: email
from: {email['from']}
subject: {email['subject']}
date: {email['date']}
priority: {priority}
gmail_id: {email['id']}
received: {datetime.now().isoformat()}
status: pending
---

## Email Summary

**From:** {email['from']}
**Subject:** {email['subject']}
**Date:** {email['date']}

**Preview:**
{email['snippet']}

## Suggested Actions

- [ ] Read full email and determine required response
- [ ] Use `skills/email-summary/SKILL.md` to draft reply
- [ ] Create approval file in `/Pending_Approval/` before replying
"""
        path = self.needs_action / f"EMAIL_{priority.upper()}_{ts}_{safe_subject}.md"
        path.write_text(content, encoding="utf-8")
        return path


if __name__ == "__main__":
    GmailWatcher().run()
