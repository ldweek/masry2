# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    request_id = fields.Many2one('purchase.request', ondelete="restrict")

    def action_view_po_request(self):
        result = {
            "name": _("Purchase Request"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.request",
            "domain": [('id', "=", self.request_id.id)],
            'view_mode': 'form',
            'res_id': self.request_id.id,
        }
        return result
