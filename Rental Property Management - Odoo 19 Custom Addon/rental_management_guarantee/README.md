# Rental Management – Tenant Bank & Insurance Guarantees

Companion Odoo 19 module for the TechKhedut **`rental_management`** addon that
registers the security instruments a tenant lodges against a lease and reminds
the responsible user before they lapse (IFCA RentX "Tenant's Bank and Insurance
Guaranteed").

## What it adds

- **`property.tenant.guarantee`** linked to a tenancy contract:
  type (Bank Guarantee / Insurance Bond / Security Guarantee / Other), guarantee
  number, issuer, amount, issue & expiry dates, responsible user, notes.
- **Lifecycle**: Draft → Active → Expired / Released / Claimed.
- **Days-to-expiry** indicator with list colour coding (red = expired,
  orange = expiring soon, grey = released/claimed).
- **Daily scheduled action** (`ir.cron`) that:
  - auto-sets lapsed Active guarantees to **Expired** (with a logged note), and
  - schedules a **reminder activity** on the responsible user when a guarantee is
    within its *Reminder Lead (days)* window (default 30).
- **Tenancy form** gains a *Guarantees* tab; menu **Properties → Tenant Guarantees**
  with search filters (Active / Expiring Soon / Expired) and group-by.

## Notes

- Amounts use the company currency.
- The "Expiring Soon" filter uses a search method (per-record reminder lead), so it
  works without storing a daily-stale flag.
- No accounting postings are made; this is a register/risk-tracking tool.

## Tested

- Python compiles, all XML well-formed, manifest & access rights valid.
- Not yet run on a live Odoo 19 instance in this environment; install + smoke test
  on staging before production use.
