# Rental Management – Move-in / Fit-out / Move-out

Companion Odoo 19 module for the TechKhedut **`rental_management`** addon that
manages the physical handover lifecycle of a leased space (IFCA RentX
"Move in, Fit Out and Move Out – Legal Documents Management").

## What it adds

- **`property.handover`** linked to a tenancy contract, one record per event:
  **Move-in**, **Fit-out** or **Move-out**.
- Type-specific fields:
  - *Fit-out*: contractor, fit-out start/end dates, fit-out bond.
  - *Condition / keys*: condition report, make-good (move-out), keys/cards
    issued & returned.
- **Checklists** with a one-click **default template per type** and a
  **progress bar** (% of items done).
- **Document management** via the chatter — attach condition reports, fit-out
  drawings, insurance certificates, permits, make-good evidence.
- Lifecycle: **Draft → In Progress → Completed / Cancelled**.
- Tenancy form gains a *Handovers* tab; menu **Properties → Handovers** with
  search filters (by type / open) and group-by.

## Default checklist templates

- **Move-in**: condition report, keys issued, insurance certificate, opening
  meter readings, welcome pack.
- **Fit-out**: drawings approved, contractor insurance, bond received, permits,
  works inspected, compliance certificates.
- **Move-out**: vacating notice, final inspection, make-good, keys returned,
  final meter readings, bond reconciled.

## Tested

- Python compiles, all XML well-formed, manifest & access rights valid.
- Not yet run on a live Odoo 19 instance in this environment; install + smoke test
  on staging before production use.
