from odoo import fields, models, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    tall = fields.Float('Tall')
    width = fields.Float('Width')
    height = fields.Float('Height')
