# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Arrears & Dunning",
    'summary': "Automated dunning ladder for overdue tenant invoices: reminder "
               "emails and optional late fees.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/cron.xml',
        'views/dunning_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
