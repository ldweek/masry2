# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'

    po_request_id = fields.Many2one('purchase.request', ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    description = fields.Char('Description')
    quantity = fields.Float('Quantity', default=1)
    uom_id = fields.Many2one('uom.uom', 'Unit')

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id
        self.description = self.product_id.name
