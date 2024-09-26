# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    tall = fields.Float('Tall')
    width = fields.Float('Width')
    height = fields.Float('Height')

    def set_products_quantity(self):
        for line in self.bom_line_ids:
            if line.product_id.product_tmpl_id.equation_id:
                result = line.product_id.product_tmpl_id.equation_id.calculate_result(self)
                line.product_qty = result

    def set_products_quantity_1(self, tall=0, width=0, height=0):
        for line in self.bom_line_ids:
            if line.product_id.product_tmpl_id.equation_id:
                result = line.product_id.product_tmpl_id.equation_id.calculate_result_1(tall, width, height)
                line.product_qty = result
