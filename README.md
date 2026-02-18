# 🤖 Digital FTE: Personal AI Employee — Master Build Plan

## What You're Building
A **fully autonomous AI employee** that:
- Monitors Gmail, WhatsApp, and your filesystem 24/7
- Reasons over tasks using Claude Code as the brain
- Acts via MCP servers (send emails, post social media, log transactions)
- Requires human approval for sensitive/risky actions
- Reports weekly CEO briefings with revenue + bottleneck analysis
- Stores everything locally in an Obsidian vault (privacy-first)

---

## Research Summary

### Core Architecture (Perception → Reasoning → Action)

```
[Gmail / WhatsApp / Bank / Files]
           ↓ (Python Watchers)
     [Obsidian Vault] ← Claude Code reads/writes here
           ↓ (Reasoning Loop)
     [Plan.md + Approval Files]
           ↓ (Human approves or auto-approved)
     [MCP Servers → External Actions]
           ↓
     [Audit Logs + Dashboard Update]
```

### Key Design Decisions
1. **Local-first** — Obsidian vault is the single source of truth. No cloud databases.
2. **File-based state** — Folder movement = state transitions (`/Needs_Action` → `/In_Progress` → `/Done`)
3. **HITL via file movement** — Human approval = move file to `/Approved`
4. **Ralph Wiggum loop** — Claude keeps iterating until all tasks in `/Needs_Action` are `/Done`
5. **Watchers as daemons** — Python scripts run forever via PM2/supervisord

### Tech Stack
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Brain | Claude Code | Reasoning engine |
| Memory/GUI | Obsidian (local Markdown) | Dashboard + long-term memory |
| Watchers | Python 3.13+ | Monitor Gmail, WhatsApp, filesystem |
| Actions | MCP Servers (Node.js) | Email, browser, calendar |
| Browser automation | Playwright | WhatsApp Web, payment portals |
| Process management | PM2 | Keep watchers alive 24/7 |
| Secrets | .env + OS keychain | Never plain-text credentials |

---

## File Structure of This Plan

```
digital-fte-plan/
├── README.md                    ← You are here
├── MASTER_SETUP.md              ← Run this first (all tiers) — includes requirements.txt + run.sh
├── VAULT_STRUCTURE.md           ← Obsidian vault layout + all templates
├── BRONZE_TIER.md               ← Foundation (8-12 hrs)
├── SILVER_TIER.md               ← Functional Assistant (20-30 hrs) — includes Browser/Payment MCP + WhatsApp SKILL
├── GOLD_TIER.md                 ← Autonomous Employee (40+ hrs) — includes Facebook, Instagram, retry_handler, watchdog
├── PLATINUM_TIER.md             ← Always-On Cloud (60+ hrs) — includes Syncthing, A2A stub, Odoo backup, git_sync.sh
├── SECURITY_GUIDE.md            ← Credential mgmt + audit logging
├── CLAUDE_CODE_PROMPTS.md       ← Ready-to-use prompts for Claude Code
└── SUBMISSION_AND_ETHICS.md     ← Submission requirements, judging criteria, ethics guide
```

## How to Use These Files With Claude Code

1. **Start Claude Code** in your vault directory: `claude --cwd ~/AI_Employee_Vault`
2. **Feed each tier file** to Claude Code as your build spec
3. **Use the prompts** in `CLAUDE_CODE_PROMPTS.md` to get Claude to build each component
4. **Work incrementally** — complete Bronze before moving to Silver

---

## Prerequisites Checklist

```bash
# Verify all tools installed
claude --version          # Claude Code
python3 --version         # Must be 3.13+
node --version            # Must be v24+
npm install -g pm2        # Process manager

# Create vault
mkdir -p ~/AI_Employee_Vault
cd ~/AI_Employee_Vault
```

Install Python dependencies (create once, reuse across tiers):
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 \
            google-api-python-client \
            playwright watchdog python-dotenv \
            requests schedule
playwright install chromium
```
