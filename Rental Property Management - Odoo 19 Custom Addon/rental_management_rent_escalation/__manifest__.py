# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Rent Escalation",
    'summary': "Scheduled periodic rent increases (fixed % or amount) on lease "
               "contracts with an escalation log.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/tenancy_views.xml',
        'views/escalation_log_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
