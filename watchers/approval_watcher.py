"""
approval_watcher.py — Watches /Approved/ folder using watchdog.

When a .md file appears in /Approved/, it:
1. Reads the frontmatter `action` field
2. Routes to the correct handler (email, social, whatsapp)
3. Calls Claude Code CLI to execute via MCP (unless DRY_RUN=true)
4. Moves the file to /Done/

Supported actions:
    send_email      — calls email MCP server
    whatsapp_reply  — logs intent (WhatsApp send is manual)
    social_post     — logs intent (social posting is manual)
"""

import os
import json
import logging
import subprocess
import time
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ApprovalWatcher] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

VAULT_PATH = Path(os.getenv("VAULT_PATH", ".")).resolve()
APPROVED_DIR = VAULT_PATH / "Approved"
DONE_DIR = VAULT_PATH / "Done"
LOGS_DIR = VAULT_PATH / "Logs"
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


# ── Frontmatter parser ────────────────────────────────────────────────────

def parse_frontmatter(content: str) -> dict:
    """Extract YAML-style frontmatter fields (simple key: value only)."""
    fields = {}
    lines = content.split("\n")
    in_block = False
    for line in lines:
        if line.strip() == "---":
            if not in_block:
                in_block = True
                continue
            else:
                break
        if in_block and ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


# ── Action handlers ───────────────────────────────────────────────────────

def handle_send_email(approval_file: Path, fields: dict):
    to = fields.get("to", "")
    subject = fields.get("subject", "")
    logging.info(f"Email action: to={to}  subject={subject}")

    if DRY_RUN:
        logging.info(f"[DRY RUN] Would call email MCP to send to: {to}")
        _append_log("send_email", approval_file.name, "dry_run", f"to={to}")
        return

    prompt = (
        f"Use the email MCP server to send an email. "
        f"Read the approval file at {approval_file} for the full content. "
        f"The approval_file path for the MCP call is: {approval_file}"
    )
    try:
        result = subprocess.run(
            ["claude", "--cwd", str(VAULT_PATH), "--print", prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        logging.info(f"Claude output: {result.stdout[:500]}")
        _append_log("send_email", approval_file.name, "success", f"to={to}")
    except subprocess.TimeoutExpired:
        logging.error("Claude timed out during email send")
        _append_log("send_email", approval_file.name, "error", "timeout")
    except Exception as exc:
        logging.error(f"Email send error: {exc}")
        _append_log("send_email", approval_file.name, "error", str(exc))


def handle_whatsapp_reply(approval_file: Path, fields: dict):
    sender = fields.get("to", fields.get("sender", "Unknown"))
    logging.info(f"WhatsApp reply action: to={sender}")
    if DRY_RUN:
        logging.info(f"[DRY RUN] Would send WhatsApp reply to: {sender}")
    else:
        logging.info(
            f"WhatsApp auto-send not implemented — open WhatsApp Web "
            f"and send the reply manually. File: {approval_file.name}"
        )
    _append_log("whatsapp_reply", approval_file.name, "dry_run" if DRY_RUN else "manual", f"to={sender}")


def handle_social_post(approval_file: Path, fields: dict):
    platform = fields.get("platform", "unknown")
    logging.info(f"Social post action: platform={platform}")
    if DRY_RUN:
        logging.info(f"[DRY RUN] Would post to {platform}")
    else:
        logging.info(
            f"Social auto-post not implemented — open {platform} and post manually. "
            f"File: {approval_file.name}"
        )
    _append_log("social_post", approval_file.name, "dry_run" if DRY_RUN else "manual", f"platform={platform}")


# ── Event handler ─────────────────────────────────────────────────────────

class ApprovalHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".md"):
            return

        filepath = Path(event.src_path)
        time.sleep(1)  # Let file finish writing

        logging.info(f"Approval file detected: {filepath.name}")
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception as exc:
            logging.error(f"Cannot read approval file: {exc}")
            return

        fields = parse_frontmatter(content)
        action = fields.get("action", "").lower()

        if action == "send_email":
            handle_send_email(filepath, fields)
        elif action == "whatsapp_reply":
            handle_whatsapp_reply(filepath, fields)
        elif action == "social_post":
            handle_social_post(filepath, fields)
        else:
            logging.warning(f"Unknown action '{action}' in {filepath.name} — skipping")
            _append_log(action or "unknown", filepath.name, "skipped", "unknown action")
            return

        # Move to Done
        done_path = DONE_DIR / filepath.name
        try:
            filepath.rename(done_path)
            logging.info(f"Moved to Done: {done_path.name}")
        except Exception as exc:
            logging.error(f"Could not move to Done: {exc}")


# ── Log helper ────────────────────────────────────────────────────────────

def _append_log(action: str, filename: str, result: str, details: str):
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "watcher": "ApprovalWatcher",
        "action": action,
        "approval_file": filename,
        "result": result,
        "details": details,
    }
    entries = []
    if log_file.exists():
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    entries.append(entry)
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


# ── Entry point ───────────────────────────────────────────────────────────

def run():
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    observer = Observer()
    observer.schedule(ApprovalHandler(), str(APPROVED_DIR), recursive=False)
    observer.start()
    logging.info(f"Watching for approvals: {APPROVED_DIR}  DRY_RUN={DRY_RUN}")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    run()
