# -*- coding: utf-8 -*-
{
    'name': "Rental Management - Property Financial Reports (Owners Statement)",
    'summary': "CBRE/MRI-style Owners Statement suite for the rental_management module: "
               "Performance Summary, Income & Expenditure (Accrual & Cash), Receipts & Payments, "
               "Tenant Balances, Aged Arrears, Payment Details, Trial Balance, Balance Sheet & GST.",
    'description': """
Property Management Financial Reporting
=======================================
Companion module that extends the TechKhedut *rental_management* addon with
property-management trust-accounting capabilities and a consolidated
**Owners Statement** report suite inspired by CBRE / MRI MRI_AUNZ output.

Adds:
 * Multi-owner per property with ownership %, property manager & contacts.
 * Financial report categories (MR-style account grouping) mapped to GL accounts.
 * Per-property / per-account budgets for Actual vs Budget vs Variance.
 * Per-property analytic account (for future cost allocation).
 * A single, sectioned Owners Statement PDF covering:
     - Performance Summary (Cash & Accrual)
     - Income & Expenditure (Accrual)
     - Receipts & Payments (Cash)
     - Tenant Balances
     - Aged Arrears
     - Payment Details
     - Trial Balance
     - Balance Sheet
     - GST Reconciliation
""",
    'author': "System Analyst (companion to TechKhedut rental_management)",
    'category': 'Realestate',
    'version': "19.0.1.0.0",
    'depends': ['rental_management', 'account', 'base_tier_validation', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/financial_category_data.xml',
        'data/remittance_sequence.xml',
        'data/tier_definition_data.xml',
        'data/management_fee_sequence.xml',
        'report/report_paperformat.xml',
        'report/owner_statement_templates.xml',
        'report/unit_inspection_templates.xml',
        'report/security_deposit_templates.xml',
        'report/clearance_certificate_templates.xml',
        'report/fitout_permit_templates.xml',
        'report/report_actions.xml',
        'views/financial_category_views.xml',
        'views/property_budget_views.xml',
        'views/property_owner_remittance_views.xml',
        'views/property_security_deposit_views.xml',
        'views/property_details_views.xml',
        'views/account_views.xml',
        'views/purchase_views.xml',
        'views/accrual_template_views.xml',
        'views/management_fee_views.xml',
        'views/period_lock_snapshot_views.xml',
        'views/unit_inspection_views.xml',
        'views/fitout_permit_views.xml',
        'wizard/owner_statement_wizard_views.xml',
        'views/menus.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
