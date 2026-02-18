# Social Media Agent Skill

## Purpose

Draft LinkedIn posts based on business updates, milestones, or content requests.
**Never auto-post** — always create an approval file in `/Pending_Approval/`.

---

## Step-by-Step Workflow

1. Read the task file in `Needs_Action/` to understand the post topic.
2. Review `Company_Handbook.md` for brand voice and key messages.
3. Draft **two versions** (A/B) of the post (see structure below).
4. Write an approval file to `/Pending_Approval/SOCIAL_LINKEDIN_<date>.md`.
5. Do NOT post directly.

---

## LinkedIn Post Structure

```
[Hook — first line, must grab attention immediately]

[Problem or insight — 2-3 lines]

[Solution or takeaway — 3-4 lines]

[CTA — question or call to action]

[Hashtags — 3-5 relevant, no more]
```

---

## Hook Formulas (pick one)

- Start with a **number**: `"3 things I learned about..."`
- Start with a **question**: `"What if you could...?"`
- Start with a **provocative statement**: `"Most [audience] get this wrong."`
- Start with a **story opener**: `"Last week, a client told me..."`

---

## Rules

- **Max 1,300 characters** per post.
- **Never** start with "Excited to share..." or "Proud to announce...".
- Write in **first person**.
- Draft **two versions** (A and B) for A/B testing.
- Hashtags: 3–5, relevant only, placed at the end.
- No emojis unless the brand voice calls for them.

---

## Approval File Format

Write to `/Pending_Approval/SOCIAL_LINKEDIN_YYYY-MM-DD.md`:

```markdown
---
action: social_post
platform: linkedin
created: [ISO timestamp]
original_file: [Needs_Action filename]
---

## Post Option A

[Full draft A text here]

---

## Post Option B

[Full draft B text here]

---

## Instructions

Review both options. Choose one, edit if needed, then move this file to `/Approved/`.
Note which option you selected in the file before moving.
To cancel, delete this file.
```
