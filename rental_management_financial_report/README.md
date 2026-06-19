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
| Trust accounting | `property.details.trust_account_id` / `remittance_account_id` / `remittance_journal_id` + `property.owner.remittance(.line)` | Opening/Closing Trust Balance, Available for Remittance, Less Remittances; posts Dr Owners Remittance / Cr Trust Bank per owner. |
| Security deposits | `property.security.deposit(.line)` + `deposit_liability_account_id` / `deposit_income_account_id` / `deposit_journal_id` | Tenant deposits tracked as a HELD LIABILITY (not income), with deductions/refunds; running balance feeds the **Sec Dep Bal** column of Tenant Balances. Optional GL posting (Dr Trust / Cr Deposit Liability on receipt). |
| Analytic | `property.details.analytic_account_id` + `account.move._post` auto-stamp | Per-property analytic account; on posting, income/expense journal items of property-linked moves are tagged with the property analytic (no distribution overwritten), so spend/income flow into Odoo's native **Analytic Accounting** (analytic items, plans, budgets, P&L by analytic). "Analytic Items" button on the property opens the standard report. |
| Linkage | `account.move.property_financial_id` (stored, computed) | Resolves the property from `tenancy_id` / `sold_id` / `maintenance_request_id` so every journal entry can be attributed to a property. |
| Report | `property.owner.statement.wizard` + QWeb PDF | One sectioned PDF with all nine reports. |

## The Owners Statement PDF contains

1. **Performance Summary** – Accrual (Income / Statutory / Variable / Direct Recharge /
   Owners Expenses / Net Return) with Actual vs Budget vs Variance vs %Var for the
   period and year-to-date, plus a **Cash Summary & Trust Reconciliation**
   (Receipts, GST, expense groups, Net Cash Before Capital, Capital, Net Cash,
   Opening Trust Balance, Available for Remittance, Less Remittances, Closing Trust Balance).
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
- **Trust accounting is modelled.** Set the Trust Bank Account, Owners Remittance Account
  and Remittance Journal on the property; record remittances under *Financial Reports →
  Owner Remittances* (use *Compute from Owners* to split by ownership %, then *Post*).
  Opening Trust Balance comes from the trust account's GL balance; Less Remittances from
  posted remittances in the period; Closing Trust Balance is derived
  (Opening + Net Cash − Remittances), mirroring the CBRE statement arithmetic.
- Tenant Balances reports all period charges under "Recurring Charges"; the
  recurring-vs-other split is not yet distinguished.

## Tested

- Python compiles, all XML is well-formed, manifest references resolve.
- Not yet run against a live Odoo 19 instance in this environment; perform an
  install + smoke test on a staging database before production use.
