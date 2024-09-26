from datetime import timedelta
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Contract(models.Model):
    _inherit = 'contract.contract'

    sale_line_id = fields.One2many('sale.order.line', compute='_get_sale_line_ids', readonly=False)


    def _get_sale_line_ids(self):
        for contract in self:
            contract.sale_line_id = self.env['sale.order.line'].search([('contract_id', '=', contract.id)]).ids


