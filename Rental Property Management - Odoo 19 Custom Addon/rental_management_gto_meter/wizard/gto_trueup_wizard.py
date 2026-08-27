# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PropertyGTOTrueupWizard(models.TransientModel):
    _name = 'property.gto.trueup.wizard'
    _description = 'Rekonsiliasi Omzet Tahunan (GTO Turnover Rent True-Up Settlement)'

    tenancy_id = fields.Many2one('tenancy.details', string='Kontrak Sewa Tenant', required=True)
    tenant_id = fields.Many2one('res.partner', related='tenancy_id.tenancy_id', store=True)
    property_id = fields.Many2one('property.details', related='tenancy_id.property_id', store=True)
    company_id = fields.Many2one('res.company', related='property_id.company_id', store=True)

    fiscal_year = fields.Selection(
        [(str(y), str(y)) for y in range(2022, 2035)],
        string='Tahun Pajak / Fiskal Audit',
        default=lambda s: str(fields.Date.today().year - 1),
        required=True
    )

    annual_audited_turnover = fields.Float(string='Realisasi Omzet Laporan Keuangan Audit (IDR)', required=True)
    turnover_percentage = fields.Float(string='Persentase Bagi Hasil (%)', default=10.0, required=True)
    calculated_turnover_rent = fields.Float(string='Kewajiban Bagi Hasil Omzet (IDR)', compute='_compute_calculations', store=True)
    total_base_rent_paid = fields.Float(string='Total Minimum Guaranteed Rent (MGR) Terbayar (IDR)', required=True)
    trueup_difference = fields.Float(string='Kekurangan Tagihan Omzet / True-Up (IDR)', compute='_compute_calculations', store=True)
    invoice_id = fields.Many2one('account.move', string='Faktur True-Up', readonly=True)

    @api.depends('annual_audited_turnover', 'turnover_percentage', 'total_base_rent_paid')
    def _compute_calculations(self):
        for rec in self:
            rec.calculated_turnover_rent = (rec.annual_audited_turnover * (rec.turnover_percentage / 100.0))
            rec.trueup_difference = max(rec.calculated_turnover_rent - rec.total_base_rent_paid, 0.0)

    def action_generate_invoice(self):
        self.ensure_one()
        if self.trueup_difference <= 0:
            raise UserError(_("Tidak ada kekurangan tagihan omzet (Realisasi omzet tidak melebihi Minimum Guaranteed Rent)."))
        if self.invoice_id:
            raise UserError(_("Faktur penyesuaian True-Up sudah pernah dibuat."))

        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.tenant_id.id,
            'invoice_date': fields.Date.today(),
            'company_id': self.company_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': f"Penyesuaian Bagi Hasil Omzet (GTO True-Up) Tahun {self.fiscal_year} - {self.property_id.name}",
                    'quantity': 1.0,
                    'price_unit': self.trueup_difference,
                }),
            ]
        })
        self.write({'invoice_id': inv.id})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Faktur True-Up Omzet',
            'res_model': 'account.move',
            'res_id': inv.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_print_report(self):
        self.ensure_one()
        return self.env.ref('rental_management_gto_meter.action_report_gto_trueup').report_action(self)
