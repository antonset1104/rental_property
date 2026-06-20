# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Parking",
    'summary': "Car-park bay register, allocation to tenants and parking rental invoicing.",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate', 'version': "19.0.1.0.0",
    'depends': ['rental_management', 'account'],
    'data': ['security/ir.model.access.csv', 'data/data.xml', 'views/parking_views.xml'],
    'license': 'LGPL-3', 'installable': True, 'application': False,
}
