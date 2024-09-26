# -*- coding: utf-8 -*-
{
    'name': "Mrp Product Quantity Calc",

    'summary': "This module contains adding functionality to calculate product quantity.",

    'description': """
        This module contains adding functionality to calculate product quantity.
    """,

    'author': "Khalid Shaheen",
    'website': "https://www.sysgates.com",
    'depends': ['base', 'mrp', 'crm', 'ad_crm_payment', 'green_contracts', 'ad_transfer_request'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/bom_pricing_wizard_view.xml',
        'wizard/pricing_menu.xml',
        'data/auto_action.xml',
        'views/equation_equation.xml',
        'views/product_template.xml',
        'views/mrp_production.xml',
        # 'views/mrp_bom.xml',
        'views/crm_lead.xml',
        'views/menus.xml',
        # 'views/config.xml',
        'views/contract.xml',
        'views/sale.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'sysgates_pro_qty_calc/static/src/components/bom_overview_control_panel/mrp_bom_control_panel.js',
    #         'sysgates_pro_qty_calc/static/src/components/bom_overview_control_panel/mrp_bom_control_panel.xml',
    #     ],
    # },
}
