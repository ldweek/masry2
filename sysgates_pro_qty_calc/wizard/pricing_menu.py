# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PricingMenu(models.TransientModel):
    _name = 'pricing.menu'

    product_id = fields.Many2one('product.product', string='Product')

    def action_open_pricing_wizard(self):
        bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)])
        vals = []
        for line in bom_id.bom_line_ids:
            vals.append((0, 0, {
                'product_id': line.product_id.id,
                'qty': line.product_qty,
            }))

        return {
            'name': _("Refund"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'bom.pricing.wizard',
            "context": {
                'default_tall': 1,
                'default_width': 1,
                'default_height': 1,
                'default_show_save': False,
                'default_wizard_line_ids': vals,
            },
            'target': 'new',
        }
