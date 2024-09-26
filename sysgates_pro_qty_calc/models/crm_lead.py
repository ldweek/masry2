# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CrmLeadLine(models.Model):
    _name = 'crm.lead.line'
    _rec_name = 'product_id'

    lead_id = fields.Many2one('crm.lead', string='Lead')
    product_id = fields.Many2one('product.product', string='Product')
    tall = fields.Float('Tall')
    width = fields.Float('Width')
    height = fields.Float('Height')
    total = fields.Float('Total')

    def open_pricing_calc_wizard(self):
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
                'default_crm_line_id': self.id,
                'default_tall': self.tall,
                'default_width': self.width,
                'default_height': self.height,
                'default_wizard_line_ids': vals,
            },
            'target': 'new',
        }


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    line_ids = fields.One2many('crm.lead.line', 'lead_id')
