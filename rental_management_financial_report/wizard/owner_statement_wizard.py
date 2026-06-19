# -*- coding: utf-8 -*-
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


class OwnerStatementWizard(models.TransientModel):
    _name = 'property.owner.statement.wizard'
    _description = 'Owners Statement Wizard'

    property_id = fields.Many2one('property.details', string='Property', required=True)
    date_from = fields.Date(string='Period From', required=True,
                            default=lambda s: date.today().replace(day=1))
    date_to = fields.Date(string='Period To', required=True, default=fields.Date.today)
    fy_start_month = fields.Selection(
        [(str(i), date(2000, i, 1).strftime('%B')) for i in range(1, 13)],
        string='Fiscal Year Starts', default='1', required=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')

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
        txt = '{:,.2f}'.format(abs(value))
        return '(%s)' % txt if neg else txt

    def _pct(self, num, den):
        if not den:
            return '0.0%'
        val = (num / den) * 100.0
        neg = val < 0
        return ('(%.1f%%)' % abs(val)) if neg else ('%.1f%%' % val)

    def _auto_section(self, account):
        at = account.account_type or ''
        if at in INCOME_TYPES:
            return 'income'
        if at in EXPENSE_TYPES:
            return 'expense'
        return 'other'

    # ----- core data ------------------------------------------------------
    def _compute_data(self):
        self.ensure_one()
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
        tenants = self._tenant_balances(lines, d_from, d_to)
        arrears = self._aged_arrears(lines, d_to)
        payments = self._payment_details(lines, d_from, d_to)
        balance = self._balance_sheet(bs)
        gst = self._gst(lines, d_from, d_to)
        cash = self._cash_data(prop, company, d_from, d_to)

        owners = [{
            'name': o.owner_id.display_name,
            'pct': '%.2f%%' % (o.ownership_percentage or 0.0),
            'city': o.owner_city or '',
        } for o in prop.owner_line_ids]

        return {
            'company': company,
            'property': prop,
            'owners': owners,
            'manager': prop.property_manager_id.name if prop.property_manager_id else '',
            'phone': prop.manager_phone or '',
            'fax': prop.manager_fax or '',
            'date_from': d_from, 'date_to': d_to,
            'fy_from': fy, 'fy_end': fy_end,
            'period_label': d_to.strftime('%B %Y'),
            'perf': perf,
            'income_exp': income_exp,
            'tenants': tenants,
            'arrears': arrears,
            'payments': payments,
            'trial': tb_rows,
            'balance': balance,
            'gst': gst,
            'cash': cash,
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
    def _tenant_balances(self, lines, d_from, d_to):
        rec_lines = lines.filtered(lambda l: l.account_id.account_type == RECEIVABLE)
        partners = {}
        for l in rec_lines:
            partners.setdefault(l.partner_id, self.env['account.move.line'])
            partners[l.partner_id] |= l
        result = []
        tot = {'beg': 0, 'rec': 0, 'oth': 0, 'cash': 0, 'end': 0}
        for partner, plines in partners.items():
            beginning = sum(x.balance for x in plines if x.date < d_from)
            charges = sum(x.debit for x in plines if d_from <= x.date <= d_to)
            receipts = sum(x.credit for x in plines if d_from <= x.date <= d_to)
            ending = sum(x.balance for x in plines)
            if (abs(beginning) < 0.005 and abs(charges) < 0.005
                    and abs(receipts) < 0.005 and abs(ending) < 0.005):
                continue
            tot['beg'] += beginning
            tot['rec'] += charges
            tot['cash'] += receipts
            tot['end'] += ending
            result.append({
                'name': partner.display_name if partner else 'Unallocated',
                'beginning': self._fmt(beginning), 'recurring': self._fmt(charges),
                'other': self._fmt(0.0), 'receipts': self._fmt(receipts),
                'ending': self._fmt(ending),
            })
        result.sort(key=lambda r: r['name'])
        totals = {'beginning': self._fmt(tot['beg']), 'recurring': self._fmt(tot['rec']),
                  'other': self._fmt(tot['oth']), 'receipts': self._fmt(tot['cash']),
                  'ending': self._fmt(tot['end'])}
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
        e_rows, e_tot = block(bs['equity'])
        net_assets = a_tot - l_tot
        return {
            'assets': a_rows, 'assets_total': self._fmt(a_tot),
            'liabilities': l_rows, 'liabilities_total': self._fmt(l_tot),
            'equity': e_rows, 'equity_total': self._fmt(e_tot),
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
        res = {'receipts': {}, 'payments': {}, 'r_total': 0.0, 'p_total': 0.0,
               'gst_r': 0.0, 'gst_p': 0.0}
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
                bucket = res['receipts'] if is_sale else res['payments']
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
                    if l.account_id.account_type not in (INCOME_TYPES + EXPENSE_TYPES):
                        continue
                    cat = l.account_id.property_fin_category_id
                    key = (cat.code or l.account_id.code or '',
                           cat.name if cat else (l.account_id.name or ''))
                    bucket[key] = bucket.get(key, 0.0) + abs(l.balance) * ratio
                if is_sale:
                    res['r_total'] += paid
                else:
                    res['p_total'] += paid
            except Exception:
                continue
        receipts = [{'code': k[0], 'name': k[1], 'amount': self._fmt(v)}
                    for k, v in sorted(res['receipts'].items())]
        payments = [{'code': k[0], 'name': k[1], 'amount': self._fmt(v)}
                    for k, v in sorted(res['payments'].items())]
        net = res['r_total'] - res['p_total']
        return {
            'receipts': receipts, 'payments': payments,
            'r_total': self._fmt(res['r_total']), 'p_total': self._fmt(res['p_total']),
            'gst_r': self._fmt(res['gst_r']), 'gst_p': self._fmt(res['gst_p']),
            'net_cash': self._fmt(net),
        }

    # ----- actions --------------------------------------------------------
    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            'rental_management_financial_report.action_report_owner_statement'
        ).report_action(self)


class OwnerStatementReport(models.AbstractModel):
    _name = 'report.rental_management_financial_report.owner_statement_document'
    _description = 'Owners Statement Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env['property.owner.statement.wizard'].browse(docids)
        statements = {w.id: w._compute_data() for w in wizards}
        return {
            'doc_ids': docids,
            'doc_model': 'property.owner.statement.wizard',
            'docs': wizards,
            'statements': statements,
        }
