# Rental Management – Property Financial Reports (Owners Statement)

Companion Odoo 19 module that extends the TechKhedut **`rental_management`** addon
with property-management trust-accounting data and a consolidated **Owners
Statement** report suite styled after CBRE / MRI MRI_AUNZ output.

> This module is intentionally a *separate* addon (depends on `rental_management`
> and `account`) so the licensed third-party module is never patched in place.

## What it adds

| Area | Object | Purpose |
|------|--------|---------|
| Multi-owner | `property.ownership.line` on `property.details` | Several owners per property with ownership %, plus Property Manager / phone / fax for the statement header. |
| Account classification | `property.financial.category` + `account.account.property_fin_category_id` | Maps GL accounts to Owners-Statement sections/sub-groups (the MRxxxx structure). |
| Budgeting | `property.budget` / `property.budget.line` | Per-property, per-account, per-month budget for Actual vs Budget vs Variance. |
| Analytic | `property.details.analytic_account_id` | Optional per-property analytic account for future cost allocation. |
| Linkage | `account.move.property_financial_id` (stored, computed) | Resolves the property from `tenancy_id` / `sold_id` / `maintenance_request_id` so every journal entry can be attributed to a property. |
| Report | `property.owner.statement.wizard` + QWeb PDF | One sectioned PDF with all nine reports. |

## The Owners Statement PDF contains

1. **Performance Summary** – Accrual (Income / Statutory / Variable / Direct Recharge /
   Owners Expenses / Net Return) with Actual vs Budget vs Variance vs %Var for the
   period and year-to-date, plus a Cash summary (Receipts / Payments / GST / Net Cash).
2. **Income & Expenditure Report (Accrual)** – per account, grouped by section &
   sub-group, with Annual Budget.
3. **Receipts & Payments Report (Cash)** – per category, Net Cash.
4. **Tenant Balances** – Beginning, Charges, Receipts, End balance per tenant.
5. **Aged Arrears Report** – Current / 1 / 2 / 3 / 4+ months buckets.
6. **Payment Details Report** – vendor bills grouped by account/supplier.
7. **Trial Balance** – Opening / Debit / Credit / Closing per account.
8. **Balance Sheet** – Assets / Liabilities / Equity / Net Assets.
9. **GST Reconciliation** – GST output vs input, net payable.

## Setup checklist (required to get populated reports)

1. Install the module (Apps → update list → install). `account.move.property_financial_id`
   is recomputed for existing entries on install.
2. **Accounting → Chart of Accounts**: set *Property Report Category* on the relevant
   income/expense accounts (or open *Properties → Financial Reports → Report Categories*).
3. **Property form → "Owners & Financial" tab**: add owners + %, Property Manager,
   phone/fax. Optionally create the analytic account.
4. **Properties → Financial Reports → Property Budgets**: enter budgets per account/month
   (use *Generate Monthly Lines* to split an annual figure ÷ 12).
5. **Properties → Financial Reports → Owners Statement**: choose property, period,
   fiscal-year start month → *Print Owners Statement*.

## Data source & scope notes (read this)

- **Accrual** figures (Performance Summary, I&E, Tenant Balances, Aged Arrears, Trial
  Balance, Balance Sheet, GST) are computed directly from **posted `account.move.line`**
  whose move is linked to the property. This is exact GL data.
- **Cash** figures (Receipts & Payments, and the Cash summary) are derived from
  **payment allocations** (`account.partial.reconcile.max_date`) within the period; they
  are a close approximation and fall back gracefully if reconciliation data is absent.
- Reports only show numbers for moves attributable to the property via
  `tenancy_id` / `sold_id` / `maintenance_request_id`. For purely manual journal entries,
  set those links (or extend `_compute_property_financial`) / use the analytic account.
- Trust-account balances (Opening/Closing Trust, Available for Remittance) and Owner
  Remittance are **not yet modelled**; the Cash summary shows Net Cash instead. These are
  the recommended next milestone (see the project mapping document in `/docs`).
- Tenant Balances reports all period charges under "Recurring Charges"; the
  recurring-vs-other split is not yet distinguished.

## Tested

- Python compiles, all XML is well-formed, manifest references resolve.
- Not yet run against a live Odoo 19 instance in this environment; perform an
  install + smoke test on a staging database before production use.
