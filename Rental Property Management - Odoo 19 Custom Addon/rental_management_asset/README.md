# Rental Management – Fixed Assets, Depreciation & Revaluation

Community-compatible fixed-asset management for the `rental_management` addon
(Odoo's native asset accounting is Enterprise-only).

## Features
- **Asset register** (`property.asset`) linked to a property: acquisition value,
  salvage, method (Straight Line / Declining Balance), number & period of
  depreciations, accounts and journal.
- **Depreciation board**: computed schedule; posting periodic journal entries
  (Dr Depreciation Expense / Cr Accumulated Depreciation), tagged to the property
  (`property_manual_id`) → flows into the Owners Statement and analytic.
- **Daily cron** auto-posts due depreciation lines.
- **Revaluation** (upward/downward): inline lines → *Post Revaluations* posts a
  journal entry against the Revaluation Reserve account (Dr Asset / Cr Reserve for
  upward; reversed for downward) and **prospectively recomputes** the remaining board.
- **CORETAX L9 sync**: *Sync CORETAX L9* creates a `coretax.asset.depreciation`
  register entry (when the coretax module is installed).

## User guide
1. Properties → **Fixed Assets** → New: property, acquisition date/value, salvage,
   method, number/period, and the accounts + journal.
2. **Compute Depreciation** → review board → **Confirm** (state Running).
3. **Post Due Depreciation** (or let the daily cron do it).
4. To revalue: add a Revaluation line (+/- amount) → **Post Revaluations**
   (board for remaining periods is recomputed on the new book value).
5. **Sync CORETAX L9** to push the asset into the annual depreciation register.

## Tested
- Python compiles, all XML well-formed, manifest & access valid; linear board math
  ties out to (gross − salvage).
- Not yet run on a live Odoo 19 instance; smoke-test on staging.
