# Rental Management – Tenant Portal

Companion Odoo 19 module for the TechKhedut **`rental_management`** addon giving
tenants a self-service area under `/my` (IFCA RentX "Tenant Portal/App").

## What it adds

- A **Contracts** card on the portal home (`/my`) with a live count.
- **`/my/contracts`** — paginated list of the logged-in tenant's own lease
  contracts (reference, property, start date, status, rent).
- **`/my/contracts/<id>`** — contract detail (property, status, payment term,
  dates, rent) with a shortcut button to the tenant's invoices (`/my/invoices`,
  provided by Odoo Accounting's portal).

## Security

- `ir.model.access`: portal group gets **read-only** access to `tenancy.details`.
- `ir.rule`: a portal user only ever sees contracts whose tenant is their own
  commercial partner (`tenancy_id child_of user.partner_id.commercial_partner_id`).
- The property name is exposed via a **stored related** field
  (`tenancy.details.portal_property_name`), so portal users never get ORM read
  access to `property.details`.
- `tenancy.details` also inherits `portal.mixin` (access token + `/my/contracts/<id>`
  access URL) for shareable document links.

## Setup

1. Install the module.
2. Give each tenant contact portal access: *Contacts → (tenant) → Action → Grant
   portal access* (standard Odoo). They can then log in and see their contracts.

## Tested

- Python compiles, all XML well-formed, manifest & access rights valid.
- Not yet run on a live Odoo 19 instance in this environment; the portal templates
  and controllers in particular should be smoke-tested on staging (portal QWeb
  inheritance hooks can vary slightly between Odoo minor versions).
