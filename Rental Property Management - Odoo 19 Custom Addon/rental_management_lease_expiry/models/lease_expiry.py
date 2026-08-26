# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class TenancyDetailsExpiry(models.Model):
    _inherit = 'tenancy.details'

    renewal_reminder_days = fields.Integer(string='Renewal Reminder (days)', default=60)
    renewal_reminder_done = fields.Boolean(copy=False)

    @api.model
    def _cron_lease_expiry_reminder(self):
        today = fields.Date.context_today(self)
        # use stored contract end date for searchability
        field = 'duration_end_date' if 'duration_end_date' in self._fields else 'end_date'
        horizon = today + relativedelta(days=90)
        try:
            candidates = self.search([(field, '!=', False), (field, '>=', today),
                                      (field, '<=', horizon)])
        except Exception:
            return True
        for rec in candidates:
            if rec.renewal_reminder_done:
                continue
            end = rec[field]
            lead = rec.renewal_reminder_days or 60
            if end and (end - today).days <= lead:
                user = rec.create_uid or self.env.user
                try:
                    rec.activity_schedule(
                        'mail.mail_activity_data_todo', date_deadline=end,
                        summary=self.env._('Lease expiring / renewal due'),
                        user_id=user.id)
                except Exception:
                    rec.message_post(body=self.env._('Lease expiring on %s.') % end)
                rec.renewal_reminder_done = True
        return True
