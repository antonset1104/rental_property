# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Property Maintenance",
    'summary': "Maintenance requests, MEP asset management, and technician inspection checklist.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_views.xml',
        'views/mep_asset_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
