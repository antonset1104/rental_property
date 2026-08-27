# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Tenant Parking",
    'summary': "Tenant parking passes, vehicle RFID registration, and quota billing.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management'],
    'data': [
        'security/ir.model.access.csv',
        'report/parking_pass_templates.xml',
        'views/parking_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
