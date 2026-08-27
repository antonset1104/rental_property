# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Rent Escalation & Lease Amendment",
    'summary': "Scheduled rent escalations, CPI indexation, lease amendments and review audit trail.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'report/amendment_templates.xml',
        'views/tenancy_views.xml',
        'views/escalation_log_views.xml',
        'views/tenancy_amendment_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
