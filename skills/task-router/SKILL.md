# Task Router Agent Skill

## Purpose

Examine a `Needs_Action/` file and route it to the correct skill.
This is the **first skill Claude reads** for every new task.

---

## Step-by-Step Workflow

1. Read the task file frontmatter — check the `type:` field.
2. If `type:` is set, use the **type-based routing** table.
3. If `type:` is missing or `unknown`, scan the body for keywords — use the **keyword routing** table.
4. Load the target skill file and follow its instructions.
5. If no skill matches, create a `Plans/REVIEW_<timestamp>.md` flagging the task for human review.

---

## Type-Based Routing

| `type:` value | Route to skill |
|--------------|---------------|
| `email` | `skills/email-summary/SKILL.md` |
| `whatsapp` | `skills/whatsapp/SKILL.md` |
| `file_drop` | Inspect file, then re-route by content |
| `invoice` | `skills/invoice-generator/SKILL.md` |
| `social` | `skills/social/SKILL.md` |
| `review` | Create review plan, flag for human |

---

## Keyword Routing (fallback)

Scan the full task file body for these keywords (case-insensitive):

| Keywords found | Route to |
|---------------|----------|
| invoice, bill, statement, billing | `skills/invoice-generator/SKILL.md` |
| payment, overdue, amount due, receipt | `skills/invoice-generator/SKILL.md` |
| whatsapp, wa, message, chat | `skills/whatsapp/SKILL.md` |
| linkedin, post, social, publish | `skills/social/SKILL.md` |
| email, reply, respond, re: | `skills/email-summary/SKILL.md` |
| (no match) | Create review plan |

---

## File-Drop Routing

When `type: file_drop`, inspect the dropped file:

| File content / extension | Route to |
|--------------------------|----------|
| `.pdf` with "invoice" in name | `skills/invoice-generator/SKILL.md` |
| `.pdf` with "contract" in name | Create review plan for human |
| `.csv` / `.xlsx` | Create review plan — likely data import |
| `.md` / `.txt` | Read and re-route by content |
| (unknown) | Create review plan |

---

## Review Plan Format

When no skill matches, write `Plans/REVIEW_YYYYMMDD_HHMMSS.md`:

```markdown
---
type: review
original_file: [task filename]
created: [ISO timestamp]
reason: [why no skill matched]
---

## Unrouted Task

**Task file:** [filename]
**Reason not auto-routed:** [explain]

## Suggested Next Steps

- [ ] Human review the task file
- [ ] Determine correct action
- [ ] Re-create task with clear `type:` frontmatter field
```

---

## Rules

- Always route to the **most specific** skill. If both `email` and `invoice` keywords match, prefer `invoice-generator`.
- Never guess financial values — route to invoice-generator and let it validate.
- If multiple tasks are in the same file, process the primary one and note the rest in the plan.
