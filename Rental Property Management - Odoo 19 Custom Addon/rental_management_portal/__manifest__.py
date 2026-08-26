# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Tenant Portal",
    'summary': "Self-service portal for tenants to view contracts, invoices, and maintenance.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'portal', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/portal_security.xml',
        'views/portal_templates.xml',
        'views/maintenance_views.xml',
        'views/announcement_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
