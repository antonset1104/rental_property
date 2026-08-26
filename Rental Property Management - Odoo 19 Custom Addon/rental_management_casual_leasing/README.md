# Rental Management – Casual Leasing

Companion Odoo 19 module for the TechKhedut **`rental_management`** addon to handle
short-term / casual lettings (promotional booths, kiosks, pop-up spaces, atrium
hire) that don't warrant a full tenancy contract (IFCA RentX "Casual Leasing").

## What it adds

- **`property.casual.lease`**: property + space/location, customer, period, and a
  **Per Day / Per Week / Fixed** rate. Billed quantity and total are computed
  automatically (`days`, `ceil(days/7)` weeks, or `1`).
- Optional deposit field.
- **One-click customer invoice** for the casual lease. If the
  `rental_management_financial_report` module is installed, the invoice is tagged
  with the property (`account.move.property_manual_id`) so it appears in the
  **Owners Statement** income; otherwise it is created as a normal invoice.
- Lifecycle: **Draft → Confirmed → Active → Done / Cancelled**.
- Menu **Properties → Casual Leases**.

## Notes

- A default *Casual Leasing* service product is created on install; map its income
  account to a Report Category for correct Owners-Statement classification.
- Decoupled from the financial-report module via a field-existence check, so it
  installs and works standalone.

## Tested

- Python compiles, all XML well-formed, manifest & access rights valid.
- Not yet run on a live Odoo 19 instance in this environment; install + smoke test
  on staging before production use.
