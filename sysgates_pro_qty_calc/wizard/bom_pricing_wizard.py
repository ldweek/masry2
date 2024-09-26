# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class BomPricingWizardLine(models.TransientModel):
    _name = 'bom.pricing.wizard.line'

    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Integer('Quantity')
    price_unit = fields.Float('Unit Price', related='product_id.lst_price')
    wizard_id = fields.Many2one('bom.pricing.wizard')


class BomPricingWizard(models.TransientModel):
    _name = 'bom.pricing.wizard'

    crm_line_id = fields.Many2one('crm.lead.line')
    show_save = fields.Boolean(default=True)
    tall = fields.Float('Tall')
    width = fields.Float('Width')
    height = fields.Float('Height')
    total = fields.Float('Total', compute='_set_total')
    wizard_line_ids = fields.One2many('bom.pricing.wizard.line', 'wizard_id')

    @api.onchange('tall', 'width', 'height')
    def set_lines_qty(self):
        for line in self.wizard_line_ids:
            line.qty = line.product_id.equation_id.calculate_result_1(self.tall, self.width, self.height)

    @api.depends('wizard_line_ids.price_unit', 'wizard_line_ids.qty')
    def _set_total(self):
        for rec in self:
            rec.total = 0
            for line in rec.wizard_line_ids:
                rec.total += line.qty * line.price_unit

    def action_save(self):
        self.crm_line_id.tall = self.tall
        self.crm_line_id.width = self.width
        self.crm_line_id.height = self.height
        self.crm_line_id.total = self.total
