# Email Summary Agent Skill

## Purpose

Read an incoming email task file, summarise it, determine the required action,
and route to the correct skill or draft a direct reply.
**Never send without an approval file in `/Pending_Approval/`.**

---

## Step-by-Step Workflow

1. Read the full `Needs_Action/EMAIL_*.md` task file.
2. Identify: sender, subject, intent (question / invoice request / complaint / other).
3. Check `CRM/Clients.md` — is this a known client?
4. **Route by keyword** (see routing table below).
5. If direct reply needed: draft reply using templates below.
6. Write a Plan to `Plans/PLAN_<timestamp>_email.md`.
7. Write an approval file to `Pending_Approval/EMAIL_REPLY_<timestamp>.md`.
8. Do NOT send directly.

---

## Routing Table

| Keyword in subject/body | Route to skill |
|------------------------|---------------|
| invoice, bill, statement | `skills/invoice-generator/SKILL.md` |
| payment, overdue, amount due | `skills/invoice-generator/SKILL.md` |
| question, help, support, how | Draft reply directly (see templates) |
| complaint, problem, error | Draft empathetic reply (see templates) |
| LinkedIn, post, social | `skills/social/SKILL.md` |
| (unknown) | Create review plan, flag for human |

---

## Reply Templates

### General Question
```
Hi [FirstName],

Thank you for reaching out. [Answer to their question, 2-3 sentences].

Please let me know if you need anything else.

Best regards,
[Company Name]
```

### Complaint / Problem
```
Hi [FirstName],

Thank you for letting us know about this. I sincerely apologise for the inconvenience.
[Specific acknowledgment of their issue].

I'm looking into this now and will get back to you with a resolution by [timeframe].

Best regards,
[Company Name]
```

### Cannot Answer (Escalate)
```
Hi [FirstName],

Thank you for your message. This has been flagged for urgent review by our team.
We'll be in touch within [1 business day / 4 hours for urgent].

Best regards,
[Company Name]
```

---

## Rules

- Always use client's **first name** only.
- Never include financial figures unless sourced from `Accounting/Rates.md`.
- Mark reply `*(AI-assisted)*` at the bottom if the email is complex.
- Keep replies under 150 words unless the topic demands more.

---

## Approval File Format

Write to `Pending_Approval/EMAIL_REPLY_YYYYMMDD_HHMMSS.md`:

```markdown
---
action: send_email
to: client@example.com
subject: Re: [original subject]
platform: gmail
priority: urgent | normal
created: [ISO timestamp]
original_file: [Needs_Action filename]
---

## Proposed Reply

[Full reply text here]

---

## Instructions

Review the reply. If approved, move this file to `/Approved/`.
The Approval Watcher will trigger the Email MCP to send it.
To cancel, delete this file.
```
