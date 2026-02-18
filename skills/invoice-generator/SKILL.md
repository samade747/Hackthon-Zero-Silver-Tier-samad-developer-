# Invoice Generator Agent Skill

## Purpose

Generate a professional invoice for a client, email it to them, and log it in Accounting.
**Always requires human approval before sending.**

---

## Step-by-Step Workflow

1. Read the task file in `Needs_Action/` to identify the client and work done.
2. Look up the client in `CRM/Clients.md`:
   - If NOT found → create a `Needs_Action` file: "Cannot generate invoice — client not in CRM".
   - If found → extract `Billing Rate`, `Currency`, `Payment Terms`, `Email`.
3. Read `Accounting/Rates.md` to confirm rates.
4. Generate an Invoice ID: `INV-YYYYMM-###` (increment from last invoice in `Accounting/Invoices/`).
5. Calculate the total:
   - Hourly: hours × rate
   - Project: fixed rate from CRM
   - Include any expenses if mentioned in the task file
6. Fill in `Templates/INVOICE_TEMPLATE.md` with all details.
7. Save the invoice to `Accounting/Invoices/INV-YYYYMM-###.md`.
8. Write a Plan to `Plans/PLAN_<timestamp>_invoice.md`.
9. Write an approval file to `Pending_Approval/INVOICE_<timestamp>.md`.
10. Do NOT email until approved.

---

## Invoice ID Generation

- Check `Accounting/Invoices/` for the most recent `INV-YYYYMM-*` file.
- Increment the last number. Start at `001` if none exist for this month.
- Example: `INV-202602-001`, `INV-202602-002`, etc.

---

## Total Calculation Rules

- Always state the rate per unit (hour / project / day).
- Always include currency symbol.
- Add VAT / tax only if `Accounting/Rates.md` specifies a tax rate.
- Round to 2 decimal places.
- If hours are not specified in the task, add a placeholder `[HOURS]` and flag for human review.

---

## Error Cases

| Situation | Action |
|-----------|--------|
| Client not in CRM | Create `Needs_Action` to add client first |
| Hours not specified | Create invoice with `[HOURS]` placeholder, note in approval file |
| Rate not in CRM or Rates.md | Flag for human, do not guess |
| Invoice folder missing | Create `Accounting/Invoices/` and continue |

---

## Approval File Format

Write to `Pending_Approval/INVOICE_YYYYMMDD_HHMMSS.md`:

```markdown
---
action: send_email
to: [client email from CRM]
subject: Invoice [INV-YYYYMM-###] from [Company Name]
platform: gmail
priority: normal
created: [ISO timestamp]
invoice_file: Accounting/Invoices/INV-YYYYMM-###.md
original_file: [Needs_Action filename]
---

## Invoice Summary

- **Client:** [Client Name]
- **Invoice ID:** INV-YYYYMM-###
- **Amount:** [Currency][Total]
- **Due Date:** [Based on Payment Terms]

## Email Body

Dear [FirstName],

Please find attached your invoice [INV-YYYYMM-###] for [description of work].

**Amount Due:** [Currency][Total]
**Due Date:** [Due Date]

Payment can be made via [payment method from CRM/Rates.md].

Thank you for your business.

Best regards,
[Company Name]

---

## Instructions

Review the invoice at `Accounting/Invoices/INV-YYYYMM-###.md`.
If approved, move this file to `/Approved/` to send the email.
To cancel, delete this file.
```
