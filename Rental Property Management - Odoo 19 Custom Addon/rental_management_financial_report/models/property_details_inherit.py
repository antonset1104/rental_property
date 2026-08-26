# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

# Names for the two analytic plans created/used by this module
_PLAN_PROPERTY = 'Properties'
_PLAN_DIVISION = 'Division'
_PLAN_SUBDIVISION = 'Sub Division'
_PLAN_DEPT = 'Department'
_PLAN_LOCATION = 'Location'


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    # Multi-owner support (IFCA / CBRE owners statement can have several owners)
    owner_line_ids = fields.One2many('property.ownership.line', 'property_id',
                                     string='Owners')
    owner_count = fields.Integer(compute='_compute_owner_count')

    # Owners Statement header information
    property_manager_id = fields.Many2one('res.users', string='Property Manager')
    manager_phone = fields.Char(string='Telephone')
    manager_fax = fields.Char(string='Facsimile')

    # Standard Unit ID & Technical MEP Specifications (PDF 2, item 6-7)
    master_unit_code = fields.Char(string='ID Unit (Master Unit)',
                                   help="Kode standar hierarki, contoh: PMKBN001-GF-01 (Gedung-Lantai-Unit).")
    unit_number = fields.Char(string='Nomor Unit')
    electricity_power_va = fields.Float(string='Daya Listrik (VA)', help="Kapasitas daya listrik unit (VA).")
    water_supply = fields.Char(string='Air Bersih', default='PDAM / Metered', help="Sumber air bersih (PDAM, Deep Well, dsb).")
    telephone_lines = fields.Integer(string='Line Telepon', default=1)
    ac_unit_count = fields.Integer(string='Jumlah Unit AC', default=0)
    has_sprinkler = fields.Boolean(string='Fire Sprinkler', default=True)
    has_smoke_detector = fields.Boolean(string='Smoke / Heat Detector', default=True)
    has_evac_speaker = fields.Boolean(string='Speaker Evakuasi / Sound', default=True)
    sewage_system = fields.Char(string='Saluran Air Kotor', default='STP Gedung')

    def action_generate_master_unit_code(self):
        """Helper to generate standard Master Unit Code: [Project/Gedung]-[Floor]-[Unit]"""
        for rec in self:
            proj = (rec.property_project_id.name or 'PROP')[:6].upper().replace(' ', '')
            floor = (rec.subproject_id.name or 'FL')[:3].upper().replace(' ', '')
            seq = rec.unit_number or rec.property_seq or str(rec.id)
            rec.master_unit_code = f"{proj}-{floor}-{seq}"
        return True

    # Per-property analytic account (Plan: Properties)
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account (Property)', copy=False)

    # Multi-level analytic dimensions (D1 gap)
    analytic_division_id = fields.Many2one(
        'account.analytic.account', string='Analytic Division', copy=False,
        help="Analytic account under the 'Division' plan for this property.")
    analytic_subdivision_id = fields.Many2one(
        'account.analytic.account', string='Analytic Sub Division', copy=False,
        help="Analytic account under the 'Sub Division' plan for this property.")
    analytic_dept_id = fields.Many2one(
        'account.analytic.account', string='Analytic Department', copy=False,
        help="Analytic account under the 'Department' plan for this property.")
    analytic_location_id = fields.Many2one(
        'account.analytic.account', string='Analytic Location', copy=False,
        help="Analytic account under the 'Location' plan for this property.")

    budget_ids = fields.One2many('property.budget', 'property_id', string='Budgets')

    # Trust accounting configuration (Owners Statement cash / remittance)
    trust_account_id = fields.Many2one(
        'account.account', string='Trust Bank Account',
        help="Bank/cash account that holds tenant funds on behalf of the owners. "
             "Its balance is reported as the Opening/Closing Trust Balance.")
    remittance_account_id = fields.Many2one(
        'account.account', string='Owners Remittance Account',
        help="Clearing account debited when funds are remitted to owners "
             "(equivalent to account '98400 Owners Remittance').")
    remittance_journal_id = fields.Many2one(
        'account.journal', string='Remittance Journal',
        domain="[('type', 'in', ('bank', 'cash', 'general'))]")
    remittance_ids = fields.One2many('property.owner.remittance', 'property_id',
                                     string='Owner Remittances')

    # Security deposit configuration (held as a liability, not income)
    deposit_liability_account_id = fields.Many2one(
        'account.account', string='Deposit Liability Account',
        help="Liability account where tenant security deposits are held.")
    deposit_income_account_id = fields.Many2one(
        'account.account', string='Deposit Forfeiture Income Account',
        help="Income account credited when part of a deposit is deducted/forfeited.")
    deposit_journal_id = fields.Many2one(
        'account.journal', string='Deposit Journal',
        domain="[('type', 'in', ('bank', 'cash', 'general'))]")
    deposit_ids = fields.One2many('property.security.deposit', 'property_id',
                                  string='Security Deposits')

    def trust_balance(self, upto_date, strict_before=False):
        """Return the GL balance of the trust account for this property
        up to (or strictly before) ``upto_date``."""
        self.ensure_one()
        if not self.trust_account_id:
            return 0.0
        company = self.company_id or self.env.company
        op = '<' if strict_before else '<='
        lines = self.env['account.move.line'].search([
            ('parent_state', '=', 'posted'),
            ('company_id', '=', company.id),
            ('move_id.property_financial_id', '=', self.id),
            ('account_id', '=', self.trust_account_id.id),
            ('date', op, upto_date)])
        return sum(lines.mapped('balance'))

    @api.depends('owner_line_ids')
    def _compute_owner_count(self):
        for rec in self:
            rec.owner_count = len(rec.owner_line_ids)

    def action_view_analytic_items(self):
        """Open the standard Analytic Items for this property's analytic account."""
        self.ensure_one()
        if not self.analytic_account_id:
            return self.action_create_analytic_account()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Analytic Items'),
            'res_model': 'account.analytic.line',
            'view_mode': 'list,form',
            'domain': [('account_id', '=', self.analytic_account_id.id)],
            'context': {'default_account_id': self.analytic_account_id.id},
        }

    def _get_or_create_plan(self, name):
        """Return (or create) an analytic plan by name."""
        Plan = self.env['account.analytic.plan'].sudo()
        plan = Plan.search([('name', '=', name)], limit=1)
        if not plan:
            plan = Plan.create({'name': name})
        return plan

    def action_create_analytic_account(self):
        """Create (once) a dedicated analytic account per dimension for the property."""
        Analytic = self.env['account.analytic.account'].sudo()
        for rec in self:
            company_vals = {'company_id': rec.company_id.id} if rec.company_id else {}
            # Property-level analytic
            if not rec.analytic_account_id:
                plan = rec._get_or_create_plan(_PLAN_PROPERTY)
                rec.analytic_account_id = Analytic.create(
                    {'name': rec.name or 'Property', 'plan_id': plan.id, **company_vals}).id
            # Division
            if not rec.analytic_division_id:
                plan = rec._get_or_create_plan(_PLAN_DIVISION)
                rec.analytic_division_id = Analytic.create(
                    {'name': rec.name or 'Property', 'plan_id': plan.id, **company_vals}).id
            # Sub Division
            if not rec.analytic_subdivision_id:
                plan = rec._get_or_create_plan(_PLAN_SUBDIVISION)
                rec.analytic_subdivision_id = Analytic.create(
                    {'name': rec.name or 'Property', 'plan_id': plan.id, **company_vals}).id
            # Department
            if not rec.analytic_dept_id:
                plan = rec._get_or_create_plan(_PLAN_DEPT)
                rec.analytic_dept_id = Analytic.create(
                    {'name': rec.name or 'Property', 'plan_id': plan.id, **company_vals}).id
            # Location
            if not rec.analytic_location_id:
                plan = rec._get_or_create_plan(_PLAN_LOCATION)
                rec.analytic_location_id = Analytic.create(
                    {'name': rec.name or 'Property', 'plan_id': plan.id, **company_vals}).id
        return True


class PropertyOwnershipLine(models.Model):
    _name = 'property.ownership.line'
    _description = 'Property Ownership Line'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    property_id = fields.Many2one('property.details', string='Property',
                                  required=True, ondelete='cascade')
    owner_id = fields.Many2one('res.partner', string='Owner', required=True)
    ownership_percentage = fields.Float(string='Ownership %', default=100.0)
    date_from = fields.Date(string='Berlaku Dari')
    date_to = fields.Date(string='Berlaku Sampai')
    owner_street = fields.Char(related='owner_id.street', string='Street')
    owner_city = fields.Char(related='owner_id.city', string='City')
    company_id = fields.Many2one(related='property_id.company_id', store=True)

    @api.constrains('ownership_percentage')
    def _check_percentage(self):
        for rec in self:
            if rec.ownership_percentage < 0 or rec.ownership_percentage > 100:
                raise ValidationError(self.env._(
                    "Ownership % must be between 0 and 100."))

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(self.env._(
                    "'Berlaku Dari' tidak boleh lebih besar dari 'Berlaku Sampai'."))


class TenancyDetailsInspection(models.Model):
    _inherit = 'tenancy.details'

    inspection_ids = fields.One2many('property.unit.inspection', 'tenancy_id', string='BAST & Inspeksi')
    inspection_count = fields.Integer(string='Jumlah BAST', compute='_compute_inspection_count')

    def _compute_inspection_count(self):
        for rec in self:
            rec.inspection_count = len(rec.inspection_ids)

    def action_view_inspections(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('BAST & Inspeksi Unit'),
            'res_model': 'property.unit.inspection',
            'view_mode': 'list,form',
            'domain': [('tenancy_id', '=', self.id)],
            'context': {
                'default_tenancy_id': self.id,
                'default_property_id': self.property_id.id if self.property_id else False,
            },
        }

