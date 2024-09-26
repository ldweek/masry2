from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.odoo.exceptions import UserError


class SupplyChainWizard(models.TransientModel):
    _name = 'supply.chain.wizard'

    location_id = fields.Many2one('stock.location', )
    location_dest_id = fields.Many2one('stock.location', )
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type')
    type = fields.Selection([
        ('stock', 'Stock'),
        ('material_request', 'Material Request'),
        ('manufacturing', 'Manufacturing')
    ], required=True)
    line_ids = fields.One2many('supply.chain.line.wizard', 'wizard_id')

    def check_product_and_quantity(self):
        ctx = self._context
        model_name = ctx.get('active_model')
        model = self.env[model_name]

        for line in self.line_ids:
            qty_remain = model.browse(line.record_id).qty_remain

            if line.quantity > qty_remain:
                raise ValidationError(_(
                    f"You cannot request more than the required quantity for {line.product_id.name}. "
                    f"Requested: {line.quantity}, Available: {qty_remain}."
                ))

    # def handle_product_and_quantity(self):
    #     # Dictionary to hold the aggregated quantities for each contract_id
    #     ctx = self.env.context
    #     contract_product_quantities = {}
    #
    #     # Iterate over the lines (recordset)
    #     for line in self.line_ids:
    #         contract_id = line.contract_id.id
    #         product_id = line.product_id.id
    #         quantity = line.quantity
    #
    #         # Initialize the contract in the dictionary if not already present
    #         if contract_id not in contract_product_quantities:
    #             contract_product_quantities[contract_id] = {}
    #
    #         # Sum quantities for each product under each contract
    #         if product_id in contract_product_quantities[contract_id]:
    #             contract_product_quantities[contract_id][product_id] += quantity
    #         else:
    #             contract_product_quantities[contract_id][product_id] = quantity
    #
    #     vals_by_contract = []
    #     for contract_id, product_quantities in contract_product_quantities.items():
    #         vals = []
    #         if ctx.get('type') == 'material_request':
    #             vals = [{'product_id': product_id, 'quantity': qty} for product_id, qty in product_quantities.items()]
    #         elif ctx.get('type') == 'stock':
    #             vals = [{'product_id': product_id, 'product_uom_qty': qty} for product_id, qty in
    #                     product_quantities.items()]
    #         vals_by_contract.append({'contract_id': contract_id, 'products': vals})
    #     return vals_by_contract

    def do_material_request(self):
        context = self.env.context
        model = context.get('active_model')

        for line in self.line_ids.filtered(lambda x: x.quantity > 0):
            ref = '% s,% s' % (model, line.record_id)
            vals = {
                'contract_id': line.contract_id.id,
                'analytic_account_id': line.analytic_account_id.id,
                'ref': ref,
                'user_id': self.env.user.id,
                'line_ids': [(0, 0, {'product_id': line.product_id.id, 'quantity': line.quantity,
                                     'unit_id': line.unit_id.id, })],
            }
            self.env['material.request'].create(vals)

            record = self.env[model].browse(line.record_id)
            record.qty_done += line.quantity

    def do_manufacturing_request(self):
        context = self.env.context
        model = context.get('active_model')

        for line in self.line_ids.filtered(lambda x: x.quantity > 0):
            ref = '% s,% s' % (model, line.record_id)

            vals = {
                'contract_id': line.contract_id.id,
                'analytic_account_id': line.analytic_account_id.id,
                'product_uom_qty': line.quantity,
                'product_id': line.product_id.id,
                'ref': ref,
                'user_request_id': self.env.user.id,
            }

            self.env['manufacturing.request'].create(vals)

            record = self.env[model].browse(line.record_id)
            record.qty_done += line.quantity

    def do_stock_request(self):
        context = self.env.context
        model = context.get('active_model')

        for line in self.line_ids.filtered(lambda x: x.quantity > 0):
            ref = '% s,% s' % (model, line.record_id)
            vals = {
                'contract_id': line.contract_id.id,
                'analytic_account_id': line.analytic_account_id.id,
                'ref': ref,
                'picking_type_id': self.picking_type_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'user_request_id': self.env.user.id,
                'move_ids_without_package': [(0, 0, {'product_id': line.product_id.id,
                                                     'product_uom_qty': line.quantity,
                                                     'name': line.product_id.name,
                                                     'location_id': self.location_id.id,
                                                     'location_dest_id': self.location_dest_id.id})],
            }

            self.env['stock.picking'].create(vals)

            record = self.env[model].browse(line.record_id)
            record.qty_done += line.quantity

    def action_request(self):
        ctx = self.env.context
        self.check_product_and_quantity()
        if ctx.get('type') == 'material_request':
            self.do_material_request()
        elif ctx.get('type') == 'stock':
            self.do_stock_request()
        elif ctx.get('type') == 'manufacturing':
            self.do_manufacturing_request()


class SupplyChainWizardLine(models.TransientModel):
    _name = 'supply.chain.line.wizard'

    wizard_id = fields.Many2one('supply.chain.wizard')
    product_id = fields.Many2one('product.product', required=True, force_save=True)
    quantity = fields.Float(required=True)
    unit_id = fields.Many2one('uom.uom', readonly=True)
    record_name = fields.Char()
    record_id = fields.Integer()
    contract_id = fields.Many2one('contract.contract')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
