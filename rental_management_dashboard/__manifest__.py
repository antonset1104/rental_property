# -*- coding: utf-8 -*-
{
    'name': "Rental Management - KPI Dashboard",
    'summary': "Management KPIs: active contracts, NOI, arrears, collection rate, "
               "lease expiry (WALE-style) per property/period.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
