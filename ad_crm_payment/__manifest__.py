# -*- coding: utf-8 -*-
{
    'name': "Crm Payment",

    'summary': 'This module contains handling of Crm Payment and related WITH Contract',

    'description': """
        This module contains handling of Crm Payment and related WITH Contract
    """,

    "author": "Sysgates _ Ahmed Eldweek",
    "license": "LGPL-3",
    "website": "https://www.sysgates.com",
    # 'category': 'Accounting & Finance',
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'sale_crm', 'sale', 'green_contracts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/crm.xml',
        'views/views_models.xml',
        'views/sale.xml',
        'views/contract.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

}
