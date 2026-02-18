"""
orchestrator.py — Silver Tier Brain Loop

Polls Needs_Action/ every 10 seconds. For each .md file found:
1. Calls Claude Code CLI with the task file path + CLAUDE.md context.
2. Claude reasons, reads skills, writes Plans/ and Pending_Approval/ files.
3. Moves the task file to In_Progress/ while processing.
4. Logs the result to Logs/YYYY-MM-DD.json.
5. Updates Dashboard.md counts.

Claude handles the actual reasoning — this script is just the trigger.
"""

import os
import json
import logging
import subprocess
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Orchestrator] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

VAULT = Path(os.getenv("VAULT_PATH", ".")).resolve()
NEEDS_ACTION = VAULT / "Needs_Action"
IN_PROGRESS = VAULT / "In_Progress"
DONE = VAULT / "Done"
LOGS_DIR = VAULT / "Logs"
POLL_INTERVAL = int(os.getenv("ORCHESTRATOR_POLL_INTERVAL", "10"))


# ── Folder setup ──────────────────────────────────────────────────────────

for folder in [NEEDS_ACTION, IN_PROGRESS, DONE, LOGS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ── Claude trigger ────────────────────────────────────────────────────────

def process_task(task_file: Path) -> str:
    """Hand a task file to Claude Code and return stdout."""
    prompt = (
        f"Read CLAUDE.md first for all instructions and rules. "
        f"Then process the task file at: Needs_Action/{task_file.name}\n"
        f"Follow CLAUDE.md instructions exactly: read the task, choose the right skill, "
        f"write a Plan, write an approval file if needed, and update Dashboard.md."
    )
    logging.info(f"Sending to Claude: {task_file.name}")
    try:
        result = subprocess.run(
            ["claude", "--cwd", str(VAULT), "--print", prompt],
            capture_output=True,
            text=True,
            timeout=300,
            encoding="utf-8",
        )
        if result.returncode != 0:
            logging.warning(f"Claude exit {result.returncode}: {result.stderr[:300]}")
        return result.stdout
    except subprocess.TimeoutExpired:
        logging.error(f"Claude timed out on {task_file.name}")
        return "ERROR: timeout"
    except FileNotFoundError:
        logging.error("'claude' CLI not found — is Claude Code installed and on PATH?")
        return "ERROR: claude not found"
    except Exception as exc:
        logging.error(f"Claude error: {exc}")
        return f"ERROR: {exc}"


# ── Log helper ────────────────────────────────────────────────────────────

def append_log(task_file: str, result: str):
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "source": "Orchestrator",
        "task_file": task_file,
        "result": "success" if not result.startswith("ERROR") else "error",
        "output_preview": result[:200],
    }
    entries = []
    if log_file.exists():
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    entries.append(entry)
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


# ── Dashboard updater ─────────────────────────────────────────────────────

def update_dashboard():
    dashboard = VAULT / "Dashboard.md"
    if not dashboard.exists():
        return
    pending = len(list(NEEDS_ACTION.glob("*.md")))
    approvals = len(list((VAULT / "Pending_Approval").glob("*.md"))) if (VAULT / "Pending_Approval").exists() else 0
    content = dashboard.read_text(encoding="utf-8")
    lines = content.splitlines()
    updated = []
    for line in lines:
        if line.startswith("Last updated:"):
            updated.append(f"Last updated: {datetime.utcnow().isoformat()}Z")
        elif line.startswith("- Pending items:"):
            updated.append(f"- Pending items: {pending}")
        elif line.startswith("- Pending approvals:"):
            updated.append(f"- Pending approvals: {approvals}")
        else:
            updated.append(line)
    dashboard.write_text("\n".join(updated), encoding="utf-8")


# ── Main loop ─────────────────────────────────────────────────────────────

def scan_and_process():
    task_files = [f for f in NEEDS_ACTION.glob("*.md") if not f.name.startswith("README")]
    if not task_files:
        return

    logging.info(f"Found {len(task_files)} task(s) to process")
    for task_file in task_files:
        # Move to In_Progress to prevent double-processing
        in_progress_path = IN_PROGRESS / task_file.name
        try:
            task_file.rename(in_progress_path)
        except Exception as exc:
            logging.error(f"Could not move {task_file.name} to In_Progress: {exc}")
            continue

        output = process_task(in_progress_path)
        append_log(task_file.name, output)

        # Move to Done after processing
        done_path = DONE / task_file.name
        try:
            in_progress_path.rename(done_path)
            logging.info(f"Done: {task_file.name}")
        except Exception as exc:
            logging.error(f"Could not move {task_file.name} to Done: {exc}")

    update_dashboard()


if __name__ == "__main__":
    logging.info(f"Orchestrator started — vault: {VAULT}  poll: {POLL_INTERVAL}s")
    while True:
        try:
            scan_and_process()
        except Exception as exc:
            logging.error(f"Orchestrator loop error: {exc}", exc_info=True)
        time.sleep(POLL_INTERVAL)
