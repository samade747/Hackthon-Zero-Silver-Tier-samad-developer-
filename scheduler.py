"""
scheduler.py — Silver Tier Scheduler

Runs two time-based Claude prompts:
    08:00 daily     — Daily briefing (checks metrics, lists tasks)
    07:00 Monday    — Weekly CEO briefing (revenue, bottlenecks, subs)

Also checks every 15 minutes for stale approvals (older than STALE_APPROVAL_HOURS).

Run via PM2 — see ecosystem.config.js.
"""

import os
import json
import logging
import subprocess
import schedule
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [Scheduler] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

VAULT = Path(os.getenv("VAULT_PATH", ".")).resolve()
LOGS_DIR = VAULT / "Logs"
BRIEFINGS_DIR = VAULT / "Briefings"
PENDING_DIR = VAULT / "Pending_Approval"
STALE_HOURS = float(os.getenv("STALE_APPROVAL_HOURS", "4"))
DAILY_TIME = os.getenv("DAILY_BRIEFING_TIME", "08:00")
WEEKLY_DAY = os.getenv("WEEKLY_BRIEFING_DAY", "monday").lower()
WEEKLY_TIME = os.getenv("WEEKLY_BRIEFING_TIME", "07:00")


# ── Claude runner ─────────────────────────────────────────────────────────

def run_claude(prompt: str, timeout: int = 300) -> str:
    """Call Claude Code CLI and return stdout."""
    logging.info(f"Running Claude prompt: {prompt[:80]}...")
    try:
        result = subprocess.run(
            ["claude", "--cwd", str(VAULT), "--print", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
        if result.returncode != 0:
            logging.warning(f"Claude exited {result.returncode}: {result.stderr[:200]}")
        return result.stdout
    except subprocess.TimeoutExpired:
        logging.error("Claude timed out")
        return ""
    except FileNotFoundError:
        logging.error("'claude' CLI not found — is Claude Code installed and on PATH?")
        return ""
    except Exception as exc:
        logging.error(f"Claude error: {exc}")
        return ""


# ── Briefing tasks ────────────────────────────────────────────────────────

def daily_briefing():
    today = datetime.now().strftime("%Y-%m-%d")
    logging.info(f"Running daily briefing for {today}")
    output = run_claude(
        f"""Generate today's daily briefing ({today}).
Steps:
1. Read Dashboard.md and note current metrics.
2. List all files in Done/ added since yesterday.
3. Count files in Needs_Action/ and Pending_Approval/.
4. Write a concise briefing to Briefings/{today}_Daily.md including:
   - Snapshot metrics
   - Tasks completed yesterday
   - Items awaiting action or approval
   - Any suggested priorities for today
5. Update Dashboard.md with current counts.
Keep the briefing under 400 words.""",
        timeout=300,
    )
    logging.info(f"Daily briefing complete. Output length: {len(output)}")
    _log_event("daily_briefing", f"Briefings/{today}_Daily.md")


def weekly_ceo_briefing():
    today = datetime.now().strftime("%Y-%m-%d")
    logging.info(f"Running Monday CEO briefing for {today}")
    output = run_claude(
        f"""Generate the Monday CEO Briefing ({today}).
Steps:
1. Read Accounting/Rates.md for current pricing.
2. Check Done/ for tasks completed this week (Mon-Sun).
3. Check Pending_Approval/ for bottlenecks (files older than 4 hours).
4. Check Accounting/Subscriptions.md for waste (if it exists).
5. Read Company_Handbook.md to understand the business context.
6. Write a structured CEO briefing to Briefings/{today}_Monday_Briefing.md:
   ## Revenue Summary
   ## Tasks Completed This Week
   ## Bottlenecks & Delays
   ## Subscription Review
   ## Recommended Actions
7. Update Dashboard.md.
Keep the briefing factual and concise.""",
        timeout=600,
    )
    logging.info(f"CEO briefing complete. Output length: {len(output)}")
    _log_event("ceo_briefing", f"Briefings/{today}_Monday_Briefing.md")


# ── Stale approval check ──────────────────────────────────────────────────

def check_stale_approvals():
    if not PENDING_DIR.exists():
        return
    now = datetime.now().timestamp()
    stale = []
    for f in PENDING_DIR.glob("*.md"):
        age_hours = (now - f.stat().st_mtime) / 3600
        if age_hours > STALE_HOURS:
            stale.append((f.name, round(age_hours, 1)))

    if stale:
        for name, age in stale:
            logging.warning(f"STALE APPROVAL ({age}h old): {name}")
        _log_event(
            "stale_check",
            f"{len(stale)} stale files: " + ", ".join(n for n, _ in stale),
        )
    else:
        logging.debug("No stale approvals")


# ── Log helper ────────────────────────────────────────────────────────────

def _log_event(event_type: str, details: str):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "source": "Scheduler",
        "event": event_type,
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


# ── Schedule setup ────────────────────────────────────────────────────────

def setup_schedule():
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)

    # Daily briefing
    schedule.every().day.at(DAILY_TIME).do(daily_briefing)
    logging.info(f"Daily briefing scheduled: {DAILY_TIME}")

    # Weekly CEO briefing (day is configurable via env)
    day_fn = getattr(schedule.every(), WEEKLY_DAY, schedule.every().monday)
    day_fn.at(WEEKLY_TIME).do(weekly_ceo_briefing)
    logging.info(f"CEO briefing scheduled: {WEEKLY_DAY} {WEEKLY_TIME}")

    # Stale approval check every 15 minutes
    schedule.every(15).minutes.do(check_stale_approvals)
    logging.info("Stale approval check: every 15 minutes")


if __name__ == "__main__":
    setup_schedule()
    logging.info("Scheduler running — press Ctrl+C to stop")
    while True:
        schedule.run_pending()
        time.sleep(60)
