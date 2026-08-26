# -*- coding: utf-8 -*-
{
    'name': "Rental Management - CAM / Service Charge",
    'summary': "Common Area Maintenance: pool expenses, apportion to tenants by "
               "area share, budget vs actual and invoice the service charge.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/cam_views.xml',
        'views/menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
