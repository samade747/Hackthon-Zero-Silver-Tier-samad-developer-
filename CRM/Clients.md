# Clients Database

## How to Add a Client

Copy the template below and fill in the details. Each client gets their own `##` section.

---

## Client Template

- **Name:**
- **Email:**
- **WhatsApp:** (optional)
- **Billing Rate:** per hour / per project
- **Payment Terms:** e.g. Net 30, due on receipt
- **Currency:** USD / GBP / PKR
- **Notes:**

---

## Sample Client — Acme Corp

- **Name:** Acme Corp
- **Contact:** John Smith
- **Email:** john.smith@acme.com
- **WhatsApp:** +1-555-000-0001
- **Billing Rate:** $150/hour
- **Payment Terms:** Net 30
- **Currency:** USD
- **Notes:** Monthly retainer. Invoice on 1st of each month.

---

## Sample Client — Beta Ltd

- **Name:** Beta Ltd
- **Contact:** Sara Khan
- **Email:** sara@betaltd.co.uk
- **WhatsApp:** +44-7700-000001
- **Billing Rate:** £1,200/project
- **Payment Terms:** 50% upfront, 50% on delivery
- **Currency:** GBP
- **Notes:** Requires invoice PDF, not markdown.

---

## Validation Rules (for AI)

When processing an invoice or reply:
1. Always look up the client by **Name** or **Email** in this file.
2. Use the **Billing Rate** and **Currency** from this file — never assume or estimate.
3. If the client is NOT listed here, create a `Needs_Action` file asking to add them first.
4. Use **Payment Terms** when writing invoice due dates.
