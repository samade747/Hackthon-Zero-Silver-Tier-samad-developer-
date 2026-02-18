# WhatsApp Agent Skill

## Purpose

Draft WhatsApp replies based on incoming messages. **Never auto-send** — always
create an approval file in `/Pending_Approval/` and wait for human approval.

---

## Step-by-Step Workflow

1. Read the `Needs_Action/WHATSAPP_*.md` file fully.
2. Identify the sender name and message intent.
3. Classify priority: **urgent** or **normal** (see keywords below).
4. Select the appropriate reply template (see below).
5. Draft a reply — max 2 sentences for urgent, 3–4 for normal.
6. Validate any financial figures against `Accounting/Rates.md`.
7. Write an approval file to `/Pending_Approval/WHATSAPP_REPLY_<timestamp>.md`.
8. Do NOT send or reply directly.

---

## Urgent Keywords

`urgent`, `asap`, `invoice`, `payment`, `help`, `problem`, `error`, `deadline`,
`critical`, `emergency`, `immediately`, `overdue`

---

## Reply Templates

### Invoice Request
```
Hi [FirstName]! Your invoice will be sent to your email within the hour.
Let me know if you need anything else!
```

### Payment Question
```
Hi [FirstName]! Let me check on that payment status for you right away.
I'll update you within the hour.
```

### Urgent / Problem
```
Hi [FirstName]! I've flagged this as urgent and someone will be with you shortly.
Thanks for letting us know.
```

### General / Normal
```
Hi [FirstName]! [Answer to their question].
Let me know if you need anything else!
```

---

## Rules

- **First name only** — never full name.
- **Max 2 sentences** for urgent (mobile reading).
- **Max 3–4 sentences** for normal.
- **Never include financial figures** unless sourced from `Accounting/Rates.md`.
- Add `*(AI-assisted)*` at the end of long or complex replies.
- Always reference client records in `CRM/Clients.md` to confirm the sender.

---

## Approval File Format

Write to `/Pending_Approval/WHATSAPP_REPLY_YYYYMMDD_HHMMSS.md`:

```markdown
---
action: whatsapp_reply
to: [SenderName]
platform: whatsapp
priority: urgent | normal
created: [ISO timestamp]
original_file: [Needs_Action filename]
---

## Proposed Reply

Hi [FirstName]! [Reply text].

---

## Instructions

Review the reply above. If approved, move this file to `/Approved/`.
To cancel, delete this file.
```
