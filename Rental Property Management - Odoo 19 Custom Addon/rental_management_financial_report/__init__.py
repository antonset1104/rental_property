# -*- coding: utf-8 -*-
from . import models
from . import wizard


def post_init_hook(env):
    analytic_group = env.ref('analytic.group_analytic_accounting', raise_if_not_found=False)
    admin_group = env.ref('base.group_system', raise_if_not_found=False)
    if analytic_group and admin_group:
        admins = env['res.users'].search([('groups_id', 'in', admin_group.ids)])
        analytic_group.sudo().write({'users': [(4, u.id) for u in admins]})
