# Rental Management – GTO & Meter Management

Companion Odoo 19 module adding two RentX-style operational capabilities on top
of the TechKhedut **`rental_management`** addon. Invoices it raises are linked to
the tenancy (`account.move.tenancy_id`), so they flow straight into the **Owners
Statement** suite (`rental_management_financial_report`) as income / tenant recharge.

## GTO (Gross Turnover) / Revenue Sharing

Configure percentage rent on a contract (**tenancy form → "GTO / Revenue Sharing" tab**):

| Field | Meaning |
|-------|---------|
| GTO Type | `Higher of Base or %`, `Base Rent + Overage`, or `Pure %` |
| Turnover % | percentage applied to declared gross turnover |
| Artificial Breakpoint | (Base + Overage) turnover threshold; 0 ⇒ natural breakpoint = base ÷ % |
| GTO Rent Product | product used on the percentage-rent invoice |

Then record **Leasing Operations → GTO Turnovers**: enter the period and gross
turnover; the **billable percentage / overage rent** is computed as:

- *Higher of*: `max(0, turnover×% − base rent)`
- *Base + Overage*: `max(0, (turnover − breakpoint) × %)`
- *Pure %*: `turnover × %`

**Create Invoice** raises a customer invoice for that amount, linked to the contract.

## Meter Management (Electricity / Water / Gas)

- **Leasing Operations → Meters**: register a meter on a property (+ current
  contract, recharge product, tariff per unit, unit label).
- **Leasing Operations → Meter Readings**: new reading auto-fills the previous
  reading from the meter's last reading; **Consumption** and **Amount**
  (`consumption × tariff`) are computed.
- **Create Recharge Invoice** bills the tenant `consumption × tariff` for the
  meter's product, linked to the contract.

## Notes

- Invoices are created in **draft** for review before posting.
- Map the GTO and Utility-Recharge products' income accounts to the appropriate
  **Property Report Category** (in the financial-report module) so they land in the
  right Owners-Statement section (Rental Income / Tenant Recharge Income).
- Default products *Percentage / GTO Rent* and *Utility Recharge* are created on install.

## Tested

- Python compiles, all XML well-formed, manifest & access rights valid.
- Not yet run on a live Odoo 19 instance in this environment; install + smoke test on
  staging before production use.
