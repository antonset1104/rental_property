# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Signature Requests",
    'summary': "Lightweight contract signature request tracking (no Enterprise "
               "Sign app required).",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate', 'version': "19.0.1.0.0",
    'depends': ['rental_management', 'mail'],
    'data': ['security/ir.model.access.csv', 'data/sequence.xml', 'views/esign_views.xml'],
    'license': 'LGPL-3', 'installable': True, 'application': False,
}
