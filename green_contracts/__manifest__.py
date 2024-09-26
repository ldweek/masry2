# -*- coding: utf-8 -*-
{
    'name': "Contracts",

    'summary': 'This module contains handling of Contract of Projects',

    'description': """
        This module contains handling of Contract of Projects
    """,

    "author": "Sysgates _ Ahmed Eldweek",
    "license": "LGPL-3",
    "website": "https://www.sysgates.com",
    # 'category': 'Accounting & Finance',
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'hr', 'product', 'account', 'sale', 'account', 'sale_crm', 'penalty_request',
                'purchase', 'crm', 'mrp', 'project', 'mrp_account', 'account_reports', 'sale_project'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_contract.xml',
        'views/contract.xml',
        'views/glass_factory.xml',
        'views/installation.xml',
        'views/manufacturing.xml',
        'views/operation.xml',
        'views/planning.xml',
        'views/purchasing.xml',
        'views/technical_office.xml',
        'views/warehouse.xml',
        'views/account.xml',
        'views/views.xml',
        'views/config.xml',
        'views/error_replacement.xml',
        'views/search.xml',
        'wizard/wizard.xml',
        'wizard/payment_wizad.xml',
        'wizard/commission.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,

}
