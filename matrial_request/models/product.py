from odoo import models, fields, api


class StockLocation(models.Model):
    _inherit = 'stock.warehouse'

    active_supply_chain = fields.Boolean(string='active supply chain', default=False)


class Product(models.Model):
    _inherit = 'product.product'

    available_quantity = fields.Float(compute='_available_quantity', store=True)

    @api.depends('qty_available')
    def _available_quantity(self):
        for product in self:
            warehouse_ids = self.env['stock.warehouse'].search([('active_supply_chain', '=', True)])
            if not warehouse_ids:
                product.available_quantity = 0.0
                continue

            location_ids = self.env['stock.location'].search(
                [('location_id', 'child_of', warehouse_ids.mapped('view_location_id').ids)])
            product_qty = sum(
                self.env['stock.quant']._get_available_quantity(product.id, location_id) for location_id in
                location_ids)
            product.available_quantity = product_qty
