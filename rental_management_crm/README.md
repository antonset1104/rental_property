# Rental Management – Leasing CRM Pipeline

Extends Odoo **CRM** for prospective-tenant management (the base addon already links
a lead to a property).

- Lead fields: expected move-in, expected rent, lease months.
- **Create Lease Contract** button: opens a new `tenancy.details` pre-filled from the
  lead (property + tenant) so required fields are completed in the standard form.
- **Lease Contracts** smart button (contracts for the lead's contact).
- "Property Leasing" sales team + "Leasing" tag.

Depends: `rental_management`, `crm`. Validated for syntax/XML; smoke-test on Odoo 19.
