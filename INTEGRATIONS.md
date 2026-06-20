# Custom Addons ↔ Standard Odoo 19 Integration Map

All custom modules are companions to the third-party **`rental_management`**
(TechKhedut) addon and integrate with standard Odoo apps as follows.

| Custom module | Standard Odoo modules used | How they integrate |
|---|---|---|
| **rental_management_financial_report** | `account` (Accounting), **Analytic Accounting** | Reads posted `account.move.line` (GL) for the Owners Statement; resolves `account.move.property_financial_id` from tenancy/sale/maintenance/manual links. Owner remittance & security-deposit post real `account.move` (Dr/Cr). **On `_post`, income/expense lines of property-linked moves are auto-tagged with the property's analytic account** → flows into native analytic items/plans/budgets. |
| **rental_management_gto_meter** | `account`, `product` | GTO turnover & meter readings create `out_invoice` linked via `tenancy_id` (→ property → reports + analytic). Uses default service products. |
| **rental_management_casual_leasing** | `account`, `product` | Creates `out_invoice`; tags `property_manual_id` when the financial module is present (field-existence check) → property attribution + analytic. |
| **rental_management_guarantee** | `mail` (Activities/Chatter) | Expiry reminders via `mail.activity`; daily `ir.cron`. |
| **rental_management_handover** | `mail` | Checklists + documents via chatter; `mail.activity.mixin`. |
| **rental_management_portal** | **`portal`** | `/my/contracts` controllers, `portal.mixin` on `tenancy.details`, record rules; links to native `/my/invoices` (Accounting portal). |
| **rental_management_coretax** | `account` | Exports posted customer invoices / vendor credit notes to CORETAX/DJP XML; taxpayer data on `res.partner`/company; e-Faktur fields on `account.move`; CORETAX codes on `product.template`. |
| **rental_management_purchase** | **`purchase`**, `account` | PO ↔ property/contract/maintenance links; `_prepare_invoice` propagates links to the vendor bill → property attribution + analytic + Payment Details. *Create PO* from a maintenance request. |
| **rental_management_crm** | **`crm`** | Leasing pipeline: leasing fields on the lead (expected move-in/rent/months), *Create Lease Contract* (opens a tenancy pre-filled from the lead), Lease Contracts smart button, "Property Leasing" team + "Leasing" tag. |
| **rental_management_project** | **`project`** (+ handover) | Turn a Fit-out handover into a `project.project` with one `project.task` per checklist item; tasks smart button. |
| **rental_management_documents** | **`documents`** (Enterprise) | One `documents.document` folder per property; push the property's `ir.attachment`s into Documents and open the folder. |
| **rental_management_asset** | `account` (+ optional coretax) | Fixed-asset register with depreciation board → posts journal entries (tagged to property → Owners Statement + analytic); revaluation against a reserve account with prospective board recompute; one-click sync to the CORETAX L9 register. |
| **rental_management_document_ce** | `rental_management` (Community) | Attachments register per property via `ir.attachment` (Community fallback for the Enterprise Documents integration). |
| **rental_management_owner_portal** | **`portal`** (+financial_report) | Owner self-service `/my/properties` with their properties and owner remittances; record rules limit to owned properties. |
| **rental_management_cam** | `account` | CAM / Service Charge: pool expenses (budget vs actual), apportion to tenants by area share, invoice the service charge (tagged to property). |
| **rental_management_rent_escalation** | `rental_management` (+cron) | Scheduled periodic rent increases (fixed % or amount) on contracts with an escalation log. |
| **rental_management_dashboard** | `account` | Management KPIs: properties, active contracts, NOI, arrears, collection rate, leases expiring in 12m (per property/period). |
| **rental_management_dunning** | `account`, `mail` (+cron) | Automated dunning ladder for overdue invoices: reminder emails (template) + optional late fees; per-move dunning level tracking. |

## Maintenance

Maintenance is **already** covered by the base `rental_management` addon (depends on
Odoo **`maintenance`**; extends `maintenance.request` with property/contract links,
tenant invoice / vendor bill, recharge and product lines). `rental_management_purchase`
adds *Create Purchase Order* from a maintenance request.

## Cross-cutting integration: Analytic Accounting

The financial-report module overrides `account.move._post` to stamp the property's
analytic account on income/expense journal items (only when empty). Because this
override is global, **every** property-linked document created by any of the custom
modules (GTO, meter, casual lease, maintenance, owner remittance, deposit,
PO-generated vendor bills) is tagged automatically — so the whole suite plugs into
Odoo's standard analytic reporting and budgeting without extra steps.

Prerequisite: give each property an analytic account (property form →
*Owners & Financial → Accounting → Create Analytic Account*).

## Notes

- Integrations are **optional/decoupled**: modules check for the presence of fields
  (e.g. `property_manual_id`) before using them, so each installs independently.
- All code is validated for syntax/XML; **smoke-test on a live Odoo 19 staging**
  database before production (view-inheritance hooks and analytic-line field names
  can vary slightly across minor versions).
