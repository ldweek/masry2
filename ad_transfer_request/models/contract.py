from odoo import fields, models


class Contract(models.Model):
    _inherit = 'contract.contract'

    distortion_count = fields.Integer(compute='compute_distortion')

    def compute_distortion(self):
        for contract in self:
            contract.distortion_count = self.env['distortion.order'].search_count([('contract_id', '=', contract.id)])

    def open_transfer_installation_wizard(self):
        action = self.env['ir.actions.act_window']._for_xml_id('ad_transfer_request.transfer_request_action_id')
        action['context'] = self.get_context_transfer()
        action['target'] = 'new'
        return action

    def get_context_transfer(self):
        sale_ids = self.env['sale.order'].search([('contract_id', '=', self.id)])
        print('function working with', sale_ids)
        vals = []
        for sale in sale_ids:
            for order in sale.order_line:
                print('order= =', order.product_uom_qty)
                if order.available_qty_to_distort > 0:
                    vals.append((0, 0, {
                        'product_id': order.product_id.id,
                        'sale_line_id': order.id,
                        'available_qty_to_distort': order.available_qty_to_distort}))

        return {
            'default_contract_id': self.id,
            'default_analytic_account_id': self.analytic_account_id.id,
            'default_partner_id': self.partner_id.id,
            'default_transfer_line_ids': vals,
        }

    def open_distortion_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Distortion Order',
            'view_type': 'tree,form',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.id)],
            'context': "{'create': False}",
            'res_model': 'distortion.order',
            'target': 'current',
        }
