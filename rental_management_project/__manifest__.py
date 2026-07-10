# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Fit-out Projects",
    'summary': "Manage tenant fit-out works as Odoo Projects/Tasks from a handover.",
    'description': """
Fit-out Projects
================
Bridges the handover module with Odoo **Project**: turn a Fit-out handover into a
project with one task per checklist item, then track the works as standard tasks.
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management_handover', 'project'],
    'data': [
        'views/handover_project_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
