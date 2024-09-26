from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import raise_error


class Transfer(models.TransientModel):
    _name = 'transfer.wizard'

    contract_id = fields.Many2one('contract.contract')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    partner_id = fields.Many2one('res.partner')
    transfer_line_ids = fields.One2many('transfer.line', 'transfer_id')

    def check_quantity(self):
        selected_products = self.transfer_line_ids.filtered(lambda line: line.selected)

        for line in selected_products:
            sale_qty = line.sale_line_id.available_qty_to_distort
            if line.available_qty_to_distort > sale_qty:
                raise UserError(
                    f"Product '{line.product_id.name}' must not exceed the available quantity ({sale_qty}) to distort.")

        return selected_products

    def action_request(self):
        selected_products = self.check_quantity()

        # Prepare values for the 'distortion.order' creation
        vals = []

        if len(selected_products) == 0:
            raise UserError("No product selected to distort.")
        for line in selected_products:
            vals.append((0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.available_qty_to_distort

            }))

        vals_create = {
            'line_ids': vals,
            'contract_id': self.contract_id.id,
            'analytic_account_id': self.analytic_account_id.id,
            'partner_id': self.partner_id.id,
        }

        # Create the distortion order
        order_id = self.env['distortion.order'].create(vals_create)

        # Prepare a dictionary with product_id as the key and available_qty_to_distort as the value
        products = {line.product_id.id: line.available_qty_to_distort for line in selected_products}

        for line in selected_products:
            line.sale_line_id.qty_distorted += line.available_qty_to_distort

        view_id = self.env.ref('ad_transfer_request.distortion_department_from_view').id
        action = {
            'name': 'Transfer Distortion',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(view_id, 'form'), (False, 'tree')],
            'res_model': 'distortion.order',
            'res_id': order_id.id,
            'target': 'current',
        }

        return action


class TransferLine(models.TransientModel):
    _name = 'transfer.line'

    sale_line_id = fields.Many2one('sale.order.line')
    product_id = fields.Many2one('product.product')
    selected = fields.Boolean(default=False)
    transfer_id = fields.Many2one('transfer.wizard')
    available_qty_to_distort = fields.Float()
