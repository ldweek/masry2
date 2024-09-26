# -*- coding: utf-8 -*-

# from odoo import models, fields, api, _
#
#
# class MrpProduction(models.Model):
#     _inherit = 'mrp.production'
#
#     tall = fields.Float('Tall')
#     width = fields.Float('Width')
#     height = fields.Float('Height')
#
#     def set_products_quantity(self):
#         for line in self.move_raw_ids:
#             if line.product_id.product_tmpl_id.equation_id:
#                 result = line.product_id.product_tmpl_id.equation_id.calculate_result(self)
#                 line.product_uom_qty = result
#                 bom_line_id = self.bom_id.bom_line_ids.filtered(lambda ln: ln.product_id.id == line.product_id.id)
#                 bom_line_id.product_qty = result
