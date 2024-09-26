# -*- coding: utf-8 -*-
{
    'name': "Purchase Request",

    'summary': "This module adding the ability to make PO requests before creating a new PO.",

    'description': """
        This module adding the ability to make PO requests before creating a new PO.
    """,

    'author': "Khalid Shaheen",
    'website': "https://www.sysgates.com",
    'depends': ['base', 'hr', 'purchase'],
    'data': [
        'data/ir_sequence_data.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/purchase_request_view.xml',
        'views/purchase_order.xml',
        'views/menus.xml',
    ],
}
