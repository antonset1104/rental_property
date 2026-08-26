# -*- coding: utf-8 -*-
import base64
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

INCOME_TYPES = ('income', 'income_other')
EXPENSE_TYPES = ('expense', 'expense_depreciation', 'expense_direct_cost')
RECEIVABLE = 'asset_receivable'
PAYABLE = 'liability_payable'

# Section -> printable header (mirrors the CBRE/MRI Income & Expenditure layout)
SECTION_LABELS = {
    'income': 'INCOME',
    'statutory': 'STATUTORY OUTGOINGS',
    'variable': 'VARIABLE OUTGOINGS',
    'direct_recharge': 'DIRECT RECHARGE',
    'tenant_recharge': 'TENANT RECHARGE EXPENDITURE',
    'non_recoverable': 'NON-RECOVERABLE EXPENDITURE',
    'capital': 'CAPITAL EXPENDITURE',
    'gst': 'GST',
    'expense': 'OTHER EXPENSES',
    'other': 'OTHER',
}
# Order of sections on the report
SECTION_ORDER = ['income', 'statutory', 'variable', 'direct_recharge',
                 'tenant_recharge', 'non_recoverable', 'expense', 'capital',
                 'gst', 'other']
# Expense sections that reduce Net Return (accrual)
EXPENSE_SECTIONS = ('statutory', 'variable', 'direct_recharge',
                    'tenant_recharge', 'non_recoverable', 'expense', 'other')


BULAN_ID = [
    '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]


class OwnerStatementWizard(models.TransientModel):
    _name = 'property.owner.statement.wizard'
    _description = 'Owners Statement Wizard'

    property_id = fields.Many2one('property.details', string='Property')
    report_mode = fields.Selection([
        ('single', 'Per Properti'),
        ('entity', 'Gabungan per Entitas / Pemilik'),
        ('consolidated', 'Konsolidasi Seluruh Entitas (16 PT)'),
    ], string='Mode Laporan', default='single', required=True)
    company_ids = fields.Many2many('res.company', string='Entitas Perusahaan (16 PT)',
                                   default=lambda s: s.env.companies,
                                   help="Pilih satu, beberapa, atau seluruh 16 PT untuk laporan konsolidasi.")
    owner_id = fields.Many2one('res.partner', string='Pemilik',
                               help='Filter properti berdasarkan pemilik (mode Entitas)')
    property_ids = fields.Many2many('property.details', string='Properti',
                                    help='Kosongkan = semua properti milik pemilik yang dipilih')
    period_type = fields.Selection([
        ('last_month', 'Last Month'),
        ('this_month', 'This Month (to date)'),
        ('last_quarter', 'Last Quarter'),
        ('this_quarter', 'This Quarter (to date)'),
        ('last_year', 'Last Financial Year'),
        ('custom', 'Custom'),
    ], string='Period', default='last_month', required=True)
    date_from = fields.Date(string='Period From', required=True,
                            default=lambda s: (date.today().replace(day=1) - relativedelta(months=1)))
    date_to = fields.Date(string='Period To', required=True,
                          default=lambda s: (date.today().replace(day=1) - relativedelta(days=1)))
    fy_start_month = fields.Selection(
        [(str(i), date(2000, i, 1).strftime('%B')) for i in range(1, 13)],
        string='Fiscal Year Starts', default='1', required=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    management_notes = fields.Text(
        string='Catatan Manajemen / Ringkasan Eksekutif',
        help="Narasi atau ringkasan kinerja dari Manajer Properti untuk dicantumkan pada laporan.")

    @api.onchange('report_mode', 'owner_id')
    def _onchange_report_mode(self):
        if self.report_mode == 'single':
            self.owner_id = False
            self.property_ids = False
        elif self.report_mode == 'entity' and self.owner_id:
            props = self.env['property.ownership.line'].search(
                [('owner_id', '=', self.owner_id.id)]).mapped('property_id')
            self.property_ids = props
            self.property_id = False

    def _get_properties(self):
        """Kembalikan recordset properti sesuai mode laporan."""
        self.ensure_one()
        if self.report_mode == 'single':
            if not self.property_id:
                raise UserError(self.env._('Pilih properti terlebih dahulu.'))
            return self.property_id
        elif self.report_mode == 'consolidated':
            dom = []
            if self.company_ids:
                dom.append(('company_id', 'in', self.company_ids.ids))
            props = self.env['property.details'].search(dom)
            if not props:
                raise UserError(self.env._('Tidak ditemukan data properti pada entitas (16 PT) yang dipilih.'))
            return props
        else:
            if self.property_ids:
                return self.property_ids
            if self.owner_id:
                return self.env['property.ownership.line'].search(
                    [('owner_id', '=', self.owner_id.id)]).mapped('property_id')
            raise UserError(self.env._('Pilih pemilik atau properti terlebih dahulu.'))

    @api.onchange('period_type', 'fy_start_month')
    def _onchange_period_type(self):
        today = date.today()
        m = int(self.fy_start_month or '1')
        if self.period_type == 'last_month':
            first_this = today.replace(day=1)
            self.date_to = first_this - relativedelta(days=1)
            self.date_from = self.date_to.replace(day=1)
        elif self.period_type == 'this_month':
            self.date_from = today.replace(day=1)
            self.date_to = today
        elif self.period_type == 'last_quarter':
            q = (today.month - 1) // 3
            if q == 0:
                q_start = date(today.year - 1, 10, 1)
            else:
                q_start = date(today.year, q * 3 - 2, 1)
            q_end = q_start + relativedelta(months=3) - relativedelta(days=1)
            self.date_from = q_start
            self.date_to = q_end
        elif self.period_type == 'this_quarter':
            q = (today.month - 1) // 3
            q_start = date(today.year, q * 3 + 1, 1)
            self.date_from = q_start
            self.date_to = today
        elif self.period_type == 'last_year':
            if today.month >= m:
                fy_start = date(today.year - 1, m, 1)
            else:
                fy_start = date(today.year - 2, m, 1)
            self.date_from = fy_start
            self.date_to = fy_start + relativedelta(years=1) - relativedelta(days=1)
        # 'custom' → biarkan user isi manual

    # ----- period helpers -------------------------------------------------
    def _periods(self):
        self.ensure_one()
        d_from, d_to = self.date_from, self.date_to
        if d_from > d_to:
            raise UserError(self.env._("'Period From' must be before 'Period To'."))
        m = int(self.fy_start_month)
        if d_to.month >= m:
            fy = date(d_to.year, m, 1)
        else:
            fy = date(d_to.year - 1, m, 1)
        fy_end = fy + relativedelta(years=1) - relativedelta(days=1)
        return d_from, d_to, fy, fy_end

    # ----- formatting -----------------------------------------------------
    def _fmt(self, value):
        value = value or 0.0
        if abs(value) < 0.005:
            value = 0.0
        neg = value < 0
        # Format Indonesia: titik pemisah ribuan, koma desimal
        txt = '{:,.2f}'.format(abs(value)).replace(',', 'X').replace('.', ',').replace('X', '.')
        return '(%s)' % txt if neg else txt

    def _pct(self, num, den):
        if not den:
            return '0,0%'
        val = (num / den) * 100.0
        neg = val < 0
        txt = '%.1f%%' % abs(val)
        return ('(%s)' % txt) if neg else txt

    def _fmt_date(self, d):
        if not d:
            return ''
        return '%d %s %d' % (d.day, BULAN_ID[d.month], d.year)

    def _fmt_period(self, d_from, d_to):
        return '%s s/d %s' % (self._fmt_date(d_from), self._fmt_date(d_to))

    def _auto_section(self, account):
        at = account.account_type or ''
        if at in INCOME_TYPES:
            return 'income'
        if at in EXPENSE_TYPES:
            return 'expense'
        return 'other'

    # ----- core data ------------------------------------------------------
    def _compute_data(self, prop=None):
        self.ensure_one()
        if prop is None:
            prop = self.property_id
        company = prop.company_id or self.company_id or self.env.company
        d_from, d_to, fy, fy_end = self._periods()
        ML = self.env['account.move.line']
        base = [('parent_state', '=', 'posted'),
                ('company_id', '=', company.id),
                ('move_id.property_financial_id', '=', prop.id)]
        lines = ML.search(base + [('date', '<=', d_to)])

        # budgets (per account, per month)
        budget_lines = self.env['property.budget.line'].search([
            ('budget_id.property_id', '=', prop.id),
            ('budget_id.state', '!=', 'cancel')])

        def bud(account_id, b_from, b_to):
            return sum(b.amount for b in budget_lines
                       if b.account_id.id == account_id and b.date
                       and b_from <= b.date <= b_to)

        # group move lines per account
        per_account = {}
        for ln in lines:
            per_account.setdefault(ln.account_id, self.env['account.move.line'])
            per_account[ln.account_id] |= ln

        pl_rows = []          # income / expense rows for I&E
        tb_rows = []          # trial balance rows
        bs = {'asset': [], 'liability': [], 'equity': []}
        for account, alines in per_account.items():
            cat = account.property_fin_category_id
            section = cat.section if cat else self._auto_section(account)
            group = (cat.group_name or cat.name) if cat else \
                (account.account_type or 'Other').replace('_', ' ').title()
            is_income = section == 'income'
            # Abatement / Rent Free is contra-income: sign stays negative so it
            # reduces total income rather than inflating expenses.
            is_abatement = cat and 'abatement' in (cat.name or '').lower()
            sign = -1.0 if is_income else 1.0

            def s(field, a, b):
                return sum(getattr(l, field) for l in alines if a <= l.date <= b)

            opening = sum(l.balance for l in alines if l.date < d_from)
            closing = sum(l.balance for l in alines)  # all <= d_to
            debit_p = s('debit', d_from, d_to)
            credit_p = s('credit', d_from, d_to)

            # Trial balance row (raw, unsigned)
            tb_rows.append({
                'code': account.code or '', 'name': account.name or '',
                'opening': self._fmt(opening), 'debit': self._fmt(debit_p),
                'credit': self._fmt(credit_p), 'closing': self._fmt(closing),
                '_sort': account.code or '',
            })

            # Balance-sheet classification
            at = account.account_type or ''
            if at.startswith('asset'):
                bs['asset'].append((account, closing))
            elif at.startswith('liability'):
                bs['liability'].append((account, -closing))
            elif at.startswith('equity'):
                bs['equity'].append((account, -closing))

            # P&L rows (income & expense only)
            if is_income or section in EXPENSE_SECTIONS or section in ('capital',):
                c_act = sign * s('balance', d_from, d_to)
                y_act = sign * s('balance', fy, d_to)
                c_bud = bud(account.id, d_from, d_to)
                y_bud = bud(account.id, fy, d_to)
                a_bud = bud(account.id, fy, fy_end)
                # favourable variance: income = actual-budget ; expense = budget-actual
                c_var = (c_act - c_bud) if is_income else (c_bud - c_act)
                y_var = (y_act - y_bud) if is_income else (y_bud - y_act)
                pl_rows.append({
                    'section': section, 'group': group,
                    'code': account.code or '', 'name': account.name or '',
                    'c_act_v': c_act, 'c_bud_v': c_bud, 'y_act_v': y_act,
                    'y_bud_v': y_bud, 'a_bud_v': a_bud,
                    'c_act': self._fmt(c_act), 'c_bud': self._fmt(c_bud),
                    'c_var': self._fmt(c_var), 'c_pct': self._pct(c_var, c_bud),
                    'y_act': self._fmt(y_act), 'y_bud': self._fmt(y_bud),
                    'y_var': self._fmt(y_var), 'y_pct': self._pct(y_var, y_bud),
                    'a_bud': self._fmt(a_bud),
                })

        tb_rows.sort(key=lambda r: r['_sort'])

        income_exp = self._build_ie(pl_rows)
        perf = self._build_performance(pl_rows, d_from, d_to, fy)
        tenants = self._tenant_balances(prop, lines, d_from, d_to)
        arrears = self._aged_arrears(lines, d_to)
        payments = self._payment_details(lines, d_from, d_to)
        balance = self._balance_sheet(bs)
        gst = self._gst(lines, d_from, d_to)
        cash_raw = self._cash_data(prop, company, d_from, d_to)
        cash_summary = self._build_cash_summary(prop, cash_raw, d_from)
        remittances = self._remittance_details(prop, d_from)
        cash = {
            'receipts': cash_raw['receipts_rows'],
            'payments': cash_raw['payments_rows'],
            'r_total': self._fmt(cash_raw['r_total']),
            'p_total': self._fmt(cash_raw['p_total']),
            'gst_r': self._fmt(cash_raw['gst_r']),
            'gst_p': self._fmt(cash_raw['gst_p']),
            'net_cash': self._fmt(cash_raw['net_cash_v']),
        }

        owners = []
        for o in prop.owner_line_ids:
            # filter ownership yang berlaku di periode laporan
            if o.date_from and o.date_from > d_to:
                continue
            if o.date_to and o.date_to < d_from:
                continue
            owners.append({
                'name': o.owner_id.display_name,
                'pct': '%.2f%%' % (o.ownership_percentage or 0.0),
                'city': o.owner_city or '',
            })

        return {
            'company': company,
            'property': prop,
            'owners': owners,
            'manager': prop.property_manager_id.name if prop.property_manager_id else '',
            'phone': prop.manager_phone or '',
            'fax': prop.manager_fax or '',
            'date_from': d_from, 'date_to': d_to,
            'fy_from': fy, 'fy_end': fy_end,
            'period_label': self._fmt_period(d_from, d_to),
            'management_notes': self.management_notes or '',
            'perf': perf,
            'income_exp': income_exp,
            'tenants': tenants,
            'arrears': arrears,
            'payments': payments,
            'trial': tb_rows,
            'balance': balance,
            'gst': gst,
            'cash': cash,
            'cash_summary': cash_summary,
            'remittances': remittances,
        }

    # ----- Income & Expenditure (accrual) ---------------------------------
    def _build_ie(self, pl_rows):
        sections = []
        income_c = income_y = income_a = 0.0
        exp_c = exp_y = exp_a = 0.0
        for sec in SECTION_ORDER:
            sec_rows = [r for r in pl_rows if r['section'] == sec]
            if not sec_rows:
                continue
            groups = {}
            for r in sec_rows:
                groups.setdefault(r['group'], []).append(r)
            group_blocks = []
            for gname, grows in groups.items():
                sub = {
                    'c_act': sum(r['c_act_v'] for r in grows),
                    'c_bud': sum(r['c_bud_v'] for r in grows),
                    'y_act': sum(r['y_act_v'] for r in grows),
                    'y_bud': sum(r['y_bud_v'] for r in grows),
                    'a_bud': sum(r['a_bud_v'] for r in grows),
                }
                group_blocks.append({
                    'label': gname, 'rows': grows,
                    'sub': {
                        'c_act': self._fmt(sub['c_act']), 'c_bud': self._fmt(sub['c_bud']),
                        'y_act': self._fmt(sub['y_act']), 'y_bud': self._fmt(sub['y_bud']),
                        'a_bud': self._fmt(sub['a_bud']),
                    },
                })
            s_c = sum(r['c_act_v'] for r in sec_rows)
            s_y = sum(r['y_act_v'] for r in sec_rows)
            s_a = sum(r['a_bud_v'] for r in sec_rows)
            sections.append({
                'key': sec, 'label': SECTION_LABELS.get(sec, sec.upper()),
                'groups': group_blocks,
                'total': {'c_act': self._fmt(s_c), 'y_act': self._fmt(s_y),
                          'a_bud': self._fmt(s_a)},
            })
            if sec == 'income':
                income_c, income_y, income_a = s_c, s_y, s_a
            elif sec in EXPENSE_SECTIONS:
                exp_c += s_c
                exp_y += s_y
                exp_a += s_a
        net_c = income_c - exp_c
        net_y = income_y - exp_y
        net_a = income_a - exp_a
        return {
            'sections': sections,
            'total_income': {'c': self._fmt(income_c), 'y': self._fmt(income_y),
                             'a': self._fmt(income_a)},
            'total_expense': {'c': self._fmt(exp_c), 'y': self._fmt(exp_y),
                              'a': self._fmt(exp_a)},
            'net_return': {'c': self._fmt(net_c), 'y': self._fmt(net_y),
                           'a': self._fmt(net_a)},
        }

    # ----- Performance Summary -------------------------------------------
    def _build_performance(self, pl_rows, d_from, d_to, fy):
        def agg(sections):
            return {
                'c_act': sum(r['c_act_v'] for r in pl_rows if r['section'] in sections),
                'c_bud': sum(r['c_bud_v'] for r in pl_rows if r['section'] in sections),
                'y_act': sum(r['y_act_v'] for r in pl_rows if r['section'] in sections),
                'y_bud': sum(r['y_bud_v'] for r in pl_rows if r['section'] in sections),
            }

        income = agg(('income',))
        statutory = agg(('statutory',))
        variable = agg(('variable',))
        direct = agg(('direct_recharge', 'tenant_recharge'))
        owners_exp = agg(('non_recoverable', 'expense', 'other'))

        def row(label, a):
            c_var = a['c_act'] - a['c_bud']
            y_var = a['y_act'] - a['y_bud']
            return {
                'label': label,
                'c_act': self._fmt(a['c_act']), 'c_bud': self._fmt(a['c_bud']),
                'c_var': self._fmt(c_var), 'c_pct': self._pct(c_var, a['c_bud']),
                'y_act': self._fmt(a['y_act']), 'y_bud': self._fmt(a['y_bud']),
                'y_var': self._fmt(y_var), 'y_pct': self._pct(y_var, a['y_bud']),
            }

        def row_exp(label, a):
            c_var = a['c_bud'] - a['c_act']
            y_var = a['y_bud'] - a['y_act']
            return {
                'label': label,
                'c_act': self._fmt(a['c_act']), 'c_bud': self._fmt(a['c_bud']),
                'c_var': self._fmt(c_var), 'c_pct': self._pct(c_var, a['c_bud']),
                'y_act': self._fmt(a['y_act']), 'y_bud': self._fmt(a['y_bud']),
                'y_var': self._fmt(y_var), 'y_pct': self._pct(y_var, a['y_bud']),
            }

        accrual_rows = [
            row('Income', income),
            row_exp('Statutory Outgoings Expenses', statutory),
            row_exp('Variable Outgoings Expenses', variable),
            row_exp('Direct Recharge Expenses', direct),
            row_exp('Owners Expenses', owners_exp),
        ]
        net = {
            'c_act': income['c_act'] - (statutory['c_act'] + variable['c_act']
                                        + direct['c_act'] + owners_exp['c_act']),
            'c_bud': income['c_bud'] - (statutory['c_bud'] + variable['c_bud']
                                        + direct['c_bud'] + owners_exp['c_bud']),
            'y_act': income['y_act'] - (statutory['y_act'] + variable['y_act']
                                        + direct['y_act'] + owners_exp['y_act']),
            'y_bud': income['y_bud'] - (statutory['y_bud'] + variable['y_bud']
                                        + direct['y_bud'] + owners_exp['y_bud']),
        }
        net_var_c = net['c_act'] - net['c_bud']
        net_var_y = net['y_act'] - net['y_bud']
        net_return = {
            'label': 'NET RETURN',
            'c_act': self._fmt(net['c_act']), 'c_bud': self._fmt(net['c_bud']),
            'c_var': self._fmt(net_var_c), 'c_pct': self._pct(net_var_c, net['c_bud']),
            'y_act': self._fmt(net['y_act']), 'y_bud': self._fmt(net['y_bud']),
            'y_var': self._fmt(net_var_y), 'y_pct': self._pct(net_var_y, net['y_bud']),
        }
        return {'accrual_rows': accrual_rows, 'net_return': net_return}

    # ----- Tenant Balances ------------------------------------------------
    def _tenant_balances(self, prop, lines, d_from, d_to):
        rec_lines = lines.filtered(lambda l: l.account_id.account_type == RECEIVABLE)
        # I3: group per (partner, tenancy) so one tenant with multiple leases
        # appears as separate rows, each identified by tenant name + contract ref + unit.
        lease_keys = {}  # (partner_id, tenancy_id) -> move.line recordset
        for l in rec_lines:
            tenancy = l.move_id.tenancy_id
            key = (l.partner_id, tenancy)
            lease_keys.setdefault(key, self.env['account.move.line'])
            lease_keys[key] |= l
        # Security deposit balances held per (tenant, tenancy)
        secdep = {}
        deposits = self.env['property.security.deposit'].search([
            ('property_id', '=', prop.id), ('state', '=', 'held')])
        for dep in deposits:
            key = (dep.tenant_id.id, dep.tenancy_id.id if dep.tenancy_id else 0)
            secdep[key] = secdep.get(key, 0.0) + dep.balance
        result = []
        tot = {'beg': 0, 'rec': 0, 'oth': 0, 'cash': 0, 'end': 0, 'sd': 0}
        for (partner, tenancy), plines in lease_keys.items():
            beginning = sum(x.balance for x in plines if x.date < d_from)
            charges = sum(x.debit for x in plines if d_from <= x.date <= d_to)
            receipts = sum(x.credit for x in plines if d_from <= x.date <= d_to)
            ending = sum(x.balance for x in plines)
            dep_key = (partner.id if partner else 0,
                       tenancy.id if tenancy else 0)
            sd = secdep.pop(dep_key, 0.0)
            if (abs(beginning) < 0.005 and abs(charges) < 0.005
                    and abs(receipts) < 0.005 and abs(ending) < 0.005
                    and abs(sd) < 0.005):
                continue
            tot['beg'] += beginning
            tot['rec'] += charges
            tot['cash'] += receipts
            tot['end'] += ending
            tot['sd'] += sd
            # Build display name: "Tenant Name | Contract Seq | Property"
            parts = [partner.display_name if partner else 'Unallocated']
            if tenancy:
                if tenancy.tenancy_seq:
                    parts.append(tenancy.tenancy_seq)
                if tenancy.property_id and tenancy.property_id != prop:
                    parts.append(tenancy.property_id.name)
            result.append({
                'name': ' | '.join(parts),
                'beginning': self._fmt(beginning), 'recurring': self._fmt(charges),
                'other': self._fmt(0.0), 'receipts': self._fmt(receipts),
                'ending': self._fmt(ending), 'secdep': self._fmt(sd),
            })
        # Deposits with no receivable activity in the period
        for (partner_id, tenancy_id), sd in secdep.items():
            if abs(sd) < 0.005:
                continue
            partner = self.env['res.partner'].browse(partner_id) if partner_id else False
            tot['sd'] += sd
            result.append({
                'name': partner.display_name if partner else 'Unallocated',
                'beginning': self._fmt(0.0), 'recurring': self._fmt(0.0),
                'other': self._fmt(0.0), 'receipts': self._fmt(0.0),
                'ending': self._fmt(0.0), 'secdep': self._fmt(sd),
            })
        result.sort(key=lambda r: r['name'])
        totals = {'beginning': self._fmt(tot['beg']), 'recurring': self._fmt(tot['rec']),
                  'other': self._fmt(tot['oth']), 'receipts': self._fmt(tot['cash']),
                  'ending': self._fmt(tot['end']), 'secdep': self._fmt(tot['sd'])}
        return {'rows': result, 'totals': totals}

    # ----- Aged Arrears ---------------------------------------------------
    def _aged_arrears(self, lines, d_to):
        rec_lines = lines.filtered(
            lambda l: l.account_id.account_type == RECEIVABLE
            and abs(l.amount_residual) > 0.005)
        partners = {}
        for l in rec_lines:
            due = l.date_maturity or l.date
            age = (d_to - due).days if due else 0
            res = l.amount_residual
            b = partners.setdefault(l.partner_id, {
                'cur': 0, 'm1': 0, 'm2': 0, 'm3': 0, 'm4': 0, 'tot': 0})
            if age <= 0:
                b['cur'] += res
            elif age <= 30:
                b['m1'] += res
            elif age <= 60:
                b['m2'] += res
            elif age <= 90:
                b['m3'] += res
            else:
                b['m4'] += res
            b['tot'] += res
        rows = []
        grand = {'cur': 0, 'm1': 0, 'm2': 0, 'm3': 0, 'm4': 0, 'tot': 0}
        for partner, b in partners.items():
            for k in grand:
                grand[k] += b[k]
            rows.append({
                'name': partner.display_name if partner else 'Unallocated',
                'current': self._fmt(b['cur']), 'm1': self._fmt(b['m1']),
                'm2': self._fmt(b['m2']), 'm3': self._fmt(b['m3']),
                'm4': self._fmt(b['m4']), 'total': self._fmt(b['tot']),
            })
        rows.sort(key=lambda r: r['name'])
        totals = {k: self._fmt(v) for k, v in
                  {'current': grand['cur'], 'm1': grand['m1'], 'm2': grand['m2'],
                   'm3': grand['m3'], 'm4': grand['m4'], 'total': grand['tot']}.items()}
        return {'rows': rows, 'totals': totals}

    # ----- Payment Details (vendor bills in period) -----------------------
    def _payment_details(self, lines, d_from, d_to):
        exp_lines = lines.filtered(
            lambda l: d_from <= l.date <= d_to
            and l.move_id.move_type in ('in_invoice', 'in_refund')
            and l.account_id.account_type in EXPENSE_TYPES)
        groups = {}
        total = 0.0
        for l in exp_lines:
            cat = l.account_id.property_fin_category_id
            key = (cat.code or l.account_id.code or '', cat.name if cat
                   else (l.account_id.name or ''))
            amt = l.balance
            total += amt
            g = groups.setdefault(key, {'rows': [], 'sum': 0.0})
            g['rows'].append({
                'supplier': l.partner_id.display_name if l.partner_id else '',
                'ref': l.move_id.name or '', 'invoice': l.move_id.ref or '',
                'date': fields.Date.to_string(l.date), 'amount': self._fmt(amt),
            })
            g['sum'] += amt
        blocks = []
        for (code, name), g in sorted(groups.items()):
            blocks.append({'code': code, 'name': name, 'rows': g['rows'],
                           'sum': self._fmt(g['sum'])})
        return {'groups': blocks, 'total': self._fmt(total)}

    # ----- Balance Sheet --------------------------------------------------
    def _balance_sheet(self, bs):
        def block(items):
            rows = []
            tot = 0.0
            for account, val in sorted(items, key=lambda x: x[0].code or ''):
                if abs(val) < 0.005:
                    continue
                tot += val
                rows.append({'code': account.code or '', 'name': account.name or '',
                             'amount': self._fmt(val)})
            return rows, tot
        a_rows, a_tot = block(bs['asset'])
        l_rows, l_tot = block(bs['liability'])
        # Split equity into Owners Contribution vs Owners Equity/Retained
        contrib_items = [(a, v) for a, v in bs['equity']
                         if a.property_fin_category_id.section == 'equity_contribution']
        retained_items = [(a, v) for a, v in bs['equity']
                          if a.property_fin_category_id.section == 'equity_retained']
        untagged_items = [(a, v) for a, v in bs['equity']
                          if a.property_fin_category_id.section
                          not in ('equity_contribution', 'equity_retained')]
        contrib_rows, contrib_tot = block(contrib_items)
        retained_rows, retained_tot = block(retained_items + untagged_items)
        e_tot = contrib_tot + retained_tot
        net_assets = a_tot - l_tot
        return {
            'assets': a_rows, 'assets_total': self._fmt(a_tot),
            'liabilities': l_rows, 'liabilities_total': self._fmt(l_tot),
            'equity_contribution': contrib_rows,
            'equity_contribution_total': self._fmt(contrib_tot),
            'equity_retained': retained_rows,
            'equity_retained_total': self._fmt(retained_tot),
            'equity_total': self._fmt(e_tot),
            'net_assets': self._fmt(net_assets),
        }

    # ----- GST Reconciliation --------------------------------------------
    def _gst(self, lines, d_from, d_to):
        tax_lines = lines.filtered(
            lambda l: l.tax_line_id and d_from <= l.date <= d_to)
        output = {}
        inp = {}
        out_tot = in_tot = 0.0
        for l in tax_lines:
            name = l.tax_line_id.name
            if l.move_id.move_type in ('out_invoice', 'out_refund'):
                output[name] = output.get(name, 0.0) + (-l.balance)
                out_tot += -l.balance
            else:
                inp[name] = inp.get(name, 0.0) + l.balance
                in_tot += l.balance
        out_rows = [{'name': k, 'amount': self._fmt(v)} for k, v in sorted(output.items())]
        in_rows = [{'name': k, 'amount': self._fmt(v)} for k, v in sorted(inp.items())]
        return {
            'output': out_rows, 'output_total': self._fmt(out_tot),
            'input': in_rows, 'input_total': self._fmt(in_tot),
            'net': self._fmt(out_tot - in_tot),
        }

    # ----- Receipts & Payments (cash basis, payment-allocation based) -----
    def _cash_data(self, prop, company, d_from, d_to):
        """Cash figures from payment allocations within the period.
        Receipt/payment amounts are NET of tax; GST is tracked separately
        (matching the CBRE 'GST on Receipts / GST on Expenses' rows)."""
        res = {'receipts': {}, 'payments': {}, 'r_total': 0.0, 'p_total': 0.0,
               'gst_r': 0.0, 'gst_p': 0.0, 'capital': 0.0,
               'by_section': dict.fromkeys(SECTION_ORDER, 0.0)}
        moves = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('company_id', '=', company.id),
            ('property_financial_id', '=', prop.id),
            ('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund'))])
        for mv in moves:
            try:
                rp = mv.line_ids.filtered(
                    lambda l: l.account_id.account_type in (RECEIVABLE, PAYABLE))
                paid = 0.0
                for l in rp:
                    parts = (l.matched_credit_ids
                             if l.account_id.account_type == RECEIVABLE
                             else l.matched_debit_ids)
                    for p in parts:
                        if p.max_date and d_from <= p.max_date <= d_to:
                            paid += p.amount
                if paid <= 0.0:
                    continue
                total = mv.amount_total or 0.0
                if not total:
                    continue
                ratio = paid / total
                is_sale = mv.move_type in ('out_invoice', 'out_refund')
                for l in mv.line_ids:
                    if l.tax_line_id:
                        g = abs(l.balance) * ratio
                        if is_sale:
                            res['gst_r'] += g
                        else:
                            res['gst_p'] += g
                        continue
                    if l.account_id.account_type in (RECEIVABLE, PAYABLE):
                        continue
                    cat = l.account_id.property_fin_category_id
                    section = cat.section if cat else self._auto_section(l.account_id)
                    amt = abs(l.balance) * ratio
                    key = (cat.code or l.account_id.code or '',
                           cat.name if cat else (l.account_id.name or ''))
                    is_income = (section == 'income') or \
                        (not cat and l.account_id.account_type in INCOME_TYPES)
                    if is_income:
                        res['receipts'][key] = res['receipts'].get(key, 0.0) + amt
                        res['r_total'] += amt
                    elif (l.account_id.account_type in EXPENSE_TYPES
                          or section in EXPENSE_SECTIONS or section == 'capital'):
                        res['payments'][key] = res['payments'].get(key, 0.0) + amt
                        res['p_total'] += amt
                        res['by_section'][section] = \
                            res['by_section'].get(section, 0.0) + amt
                        if section == 'capital':
                            res['capital'] += amt
            except Exception:
                continue
        receipts = [{'code': k[0], 'name': k[1], 'amount': self._fmt(v)}
                    for k, v in sorted(res['receipts'].items())]
        payments = [{'code': k[0], 'name': k[1], 'amount': self._fmt(v)}
                    for k, v in sorted(res['payments'].items())]
        net_cash = (res['r_total'] - res['p_total']) + (res['gst_r'] - res['gst_p'])
        res.update({
            'receipts_rows': receipts, 'payments_rows': payments,
            'net_cash_v': net_cash,
        })
        return res

    # ----- Performance Summary: Cash + Trust roll-forward -----------------
    def _build_cash_summary(self, prop, cash, d_from):
        bysec = cash['by_section']
        statutory = bysec.get('statutory', 0.0)
        variable = bysec.get('variable', 0.0)
        direct = bysec.get('direct_recharge', 0.0) + bysec.get('tenant_recharge', 0.0)
        non_recov = (bysec.get('non_recoverable', 0.0) + bysec.get('expense', 0.0)
                     + bysec.get('other', 0.0))
        capital = cash['capital']
        ncbc = cash['net_cash_v'] + capital  # net cash before capital
        net_cash = cash['net_cash_v']

        # Trust roll-forward
        opening_trust = prop.trust_balance(d_from, strict_before=True)
        remittances = self._period_remittances(prop, d_from)
        available = net_cash + opening_trust
        closing_trust = available - remittances

        rows = [
            {'label': 'Receipts', 'v': self._fmt(cash['r_total'])},
            {'label': 'GST on Receipts', 'v': self._fmt(cash['gst_r'])},
            {'label': 'Statutory Outgoings Expense', 'v': self._fmt(statutory)},
            {'label': 'Variable Outgoings Expense', 'v': self._fmt(variable)},
            {'label': 'Direct Recharge Expense', 'v': self._fmt(direct)},
            {'label': 'Non-Recoverable Expenses', 'v': self._fmt(non_recov)},
            {'label': 'GST on Expenses', 'v': self._fmt(cash['gst_p'])},
            {'label': 'NET CASH BEFORE CAPITAL', 'v': self._fmt(ncbc), 'bold': True},
            {'label': 'Capital', 'v': self._fmt(capital)},
            {'label': 'NET CASH', 'v': self._fmt(net_cash), 'bold': True},
            {'label': 'Opening Trust Balance', 'v': self._fmt(opening_trust)},
            {'label': 'AVAILABLE FOR REMITTANCE', 'v': self._fmt(available), 'bold': True},
            {'label': 'Less Remittances', 'v': self._fmt(remittances)},
            {'label': 'CLOSING TRUST BALANCE', 'v': self._fmt(closing_trust), 'bold': True},
        ]
        return rows

    def _period_remittances(self, prop, d_from):
        rems = self.env['property.owner.remittance'].search([
            ('property_id', '=', prop.id), ('state', '=', 'posted'),
            ('date', '>=', d_from), ('date', '<=', self.date_to)])
        return sum(rems.mapped('total_amount'))

    def _remittance_details(self, prop, d_from):
        rems = self.env['property.owner.remittance'].search([
            ('property_id', '=', prop.id), ('state', '=', 'posted'),
            ('date', '>=', d_from), ('date', '<=', self.date_to)])
        rows = []
        total = 0.0
        for rem in rems:
            for line in rem.line_ids:
                total += line.amount
                rows.append({
                    'supplier': line.owner_id.display_name,
                    'ref': rem.name,
                    'date': fields.Date.to_string(rem.date),
                    'amount': self._fmt(line.amount),
                })
        return {'rows': rows, 'total': self._fmt(total)}

    # ----- actions --------------------------------------------------------
    def _check_period_lock(self, prop, d_from, d_to):
        """Raise if the requested period overlaps an active lock for this property."""
        lock = self.env['property.period.lock'].search([
            ('property_id', '=', prop.id),
            ('active', '=', True),
            ('date_from', '<=', d_to),
            ('date_to', '>=', d_from),
        ], limit=1)
        if lock:
            raise UserError(
                self.env._(
                    "Period %s – %s for property '%s' is locked (reason: %s). "
                    "Unlock it first via Financial Reports > Period Locks."
                ) % (d_from, d_to, prop.name, lock.reason or ''))

    def action_print(self):
        self.ensure_one()
        props = self._get_properties()
        d_from, d_to = self.date_from, self.date_to
        # P2: check period lock before generating
        for prop in props:
            self._check_period_lock(prop, d_from, d_to)
        if self.report_mode == 'single':
            self.property_id = props.id
        else:
            self.property_ids = props
        # P3: save permanent snapshot for each property
        # Strip non-serialisable recordset keys before saving JSON
        Snapshot = self.env['property.report.snapshot']
        for prop in props:
            data = self._compute_data(prop)
            snap_data = {k: v for k, v in data.items()
                         if k not in ('company', 'property')}
            snap_data['property_name'] = prop.name or ''
            snap_data['company_name'] = (prop.company_id.name
                                         or self.env.company.name or '')
            Snapshot.save_snapshot(prop.id, d_from, d_to, snap_data)
        return self.env.ref(
            'rental_management_financial_report.action_report_owner_statement'
        ).report_action(self)

    def action_send_email_to_owners(self):
        self.ensure_one()
        props = self._get_properties()
        d_from, d_to = self.date_from, self.date_to
        for prop in props:
            self._check_period_lock(prop, d_from, d_to)

        report = self.env.ref('rental_management_financial_report.action_report_owner_statement')
        pdf_content, _ = report._render_qweb_pdf('rental_management_financial_report.action_report_owner_statement', res_ids=self.ids)

        owners = self.env['res.partner']
        if self.report_mode == 'single' and self.property_id:
            owners = self.property_id.owner_line_ids.mapped('owner_id')
            if not owners and hasattr(self.property_id, 'property_owner_id') and self.property_id.property_owner_id:
                owners = self.property_id.property_owner_id
        elif self.owner_id:
            owners = self.owner_id
        else:
            for p in props:
                owners |= p.owner_line_ids.mapped('owner_id')

        if not owners:
            raise UserError(self.env._("Tidak ditemukan kontak pemilik (Owner) untuk dikirimkan laporan."))

        sent_count = 0
        period_str = self._fmt_period(d_from, d_to)
        for owner in owners:
            if not owner.email:
                continue
            attachment = self.env['ir.attachment'].create({
                'name': f"Owners_Statement_{period_str.replace(' ', '_')}.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'property.owner.statement.wizard',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            notes_html = f"<p><b>Catatan Manajemen:</b><br/>{self.management_notes}</p>" if self.management_notes else ""
            body_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 13px; color: #333;">
                <p>Kepada Yth. <b>{owner.name}</b>,</p>
                <p>Terlampir kami sampaikan <b>Laporan Pemilik (Owners Statement)</b> untuk periode <b>{period_str}</b>.</p>
                <p>Laporan mencakup ringkasan kinerja akrual, mutasi arus kas, rekonsiliasi saldo titipan, serta rincian pembayaran sewa tenant.</p>
                {notes_html}
                <p>Apabila terdapat pertanyaan, silakan menghubungi tim Property Management kami.</p>
                <br/>
                <p>Hormat kami,<br/><b>{self.env.company.name}</b><br/>Property Management Division</p>
            </div>
            """
            mail = self.env['mail.mail'].create({
                'subject': f"Laporan Pemilik (Owners Statement) - Periode {period_str}",
                'body_html': body_html,
                'email_to': owner.email,
                'attachment_ids': [(4, attachment.id)],
            })
            mail.send()
            sent_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Email Terkirim'),
                'message': self.env._('Laporan Pemilik berhasil dikirimkan via email ke %s pemilik.') % sent_count,
                'type': 'success',
                'sticky': False,
            }
        }



class OwnerStatementReport(models.AbstractModel):
    _name = 'report.rental_management_financial_report.owner_statement_document'
    _table = 'report_rmfr_owner_statement_doc'
    _description = 'Owners Statement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env['property.owner.statement.wizard'].browse(docids)
        statements = {}
        for w in wizards:
            props = w._get_properties()
            if w.report_mode == 'single':
                statements[w.id] = [w._compute_data(props)]
            else:
                statements[w.id] = [w._compute_data(p) for p in props]
        return {
            'doc_ids': docids,
            'doc_model': 'property.owner.statement.wizard',
            'docs': wizards,
            'statements': statements,
        }
