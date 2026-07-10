# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Owner Portal",
    'summary': "Self-service portal for property owners: their properties and "
               "owner remittances.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management_financial_report', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'security/owner_portal_security.xml',
        'views/portal_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
