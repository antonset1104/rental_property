# Rental Management – Fit-out Projects

Bridges the handover module with Odoo **Project**.

- On a Fit-out handover: **Create Fit-out Project** builds a `project.project` and one
  `project.task` per checklist item; **Fit-out Tasks** smart button opens them.
- `project_id` shown on fit-out handovers.

Depends: `rental_management_handover`, `project`. Validated for syntax/XML; smoke-test on Odoo 19.
