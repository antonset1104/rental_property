# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Documents (Community)",
    'summary': "Attachments and legal documents register per property.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/property_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
