# Rental Management – Property Procurement (Purchase)

Companion Odoo 19 module integrating the standard **Purchase** app with the
TechKhedut **`rental_management`** addon, so property spend follows a real
RFQ → PO → receipt → vendor bill flow instead of ad-hoc direct bills.

## What it adds

- **Purchase Order** (*Property* tab): `Property`, `Lease Contract`, `Maintenance
  Request` links (contract/maintenance auto-fill the property).
- **Bill propagation**: `purchase.order._prepare_invoice()` copies those links to
  the generated vendor bill (`account.move.tenancy_id` / `maintenance_request_id`,
  and `property_manual_id` when the financial-report module is installed). The spend
  is therefore attributed to the property and appears in the Owners Statement
  **Payment Details**.
- **Maintenance Request**: a *Create Purchase Order* header button (uses the request's
  product lines and vendor) and a Purchase Orders smart button.
- **Properties → Property Purchase Orders** menu (POs that carry a property).

## Why

The base addon records vendor spend as direct vendor bills (no RFQ/PO/approval/
receipt). This module lets you use Odoo's full procurement flow while keeping the
spend linked to the property — and gives the CBRE-style Payment Details report its
PO origin.

## Tested

- Python compiles, all XML well-formed, manifest valid (no new models → standard
  Purchase/Maintenance access rights apply).
- Not yet run on a live Odoo 19 instance; smoke-test on staging (view inheritance
  hooks `purchase.purchase_order_form` and `maintenance.hr_equipment_request_view_form`
  should be confirmed for your exact version).
