# -*- coding: utf-8 -*-
{
    'name': "Form Contract and Prints",

    'summary': 'This module contains handling of Form Contract and Prints',

    'description': """
        This module contains handling of Form Contract and Prints
    """,

    "author": "Sysgates _ Ahmed Eldweek",
    "license": "LGPL-3",
    "website": "https://www.sysgates.com",
    # 'category': 'Accounting & Finance',
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'green_contracts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/form_contract.xml',
        'reports/report_action.xml',
        'reports/template.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,

}
