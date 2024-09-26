from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    contract_id = fields.Many2one('contract.contract')
    material_id = fields.Many2one('material.request')
    user_request_id = fields.Many2one('res.users', readonly=True)
    mr_count = fields.Integer(compute='_compute_mr_count')

    def _compute_mr_count(self):
        for order in self:
            material_lines = order.order_line.mapped('material_line_id')
            order.mr_count = self.env['material.request'].search_count(
                [('line_ids', 'in', material_lines.ids)]) if material_lines else 0

    def open_material_request_action(self):
        self.ensure_one()
        action = {
            'name': _("Material Request list"),
            'type': 'ir.actions.act_window',
            'res_model': 'material.request',
            'context': {'create': False},
        }

        material_lines = self.order_line.mapped('material_line_id')
        material_id = self.env['material.request'].search([('line_ids', 'in', material_lines.ids)])

        if len(material_id) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': material_id.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', material_id.ids)],
            })
        return action

    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s", self.partner_id.name))
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
            'state': 'draft',
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    contract_id = fields.Many2one('contract.contract')
    material_line_id = fields.Many2one('material.request.line')

    @api.model_create_multi
    def create(self, vals_list):
        """
        Create multiple records with additional logic for material requests.

        :param vals_list: List of dictionaries with record values
        :return: Created records
        """
        for vals in vals_list:
            if 'material_line_id' in vals:
                material_line_id = vals['material_line_id']
                material_line = self.env['material.request.line'].browse(material_line_id).exists()

                if material_line:
                    material_id = material_line.material_request_id
                    domain = [('material_line_id', '=', material_line_id), ('state', '!=', 'cancel')]
                    purchase_lines = self.env['purchase.order.line'].search(domain)
                    quantity_old_purchase = sum(purchase_lines.mapped('product_qty'))
                    new_qty = vals.get('product_qty')
                    quantity_all_purchase = new_qty + quantity_old_purchase

                    if quantity_all_purchase > material_line.quantity:
                        max_qty = material_line.quantity - quantity_old_purchase
                        raise UserError(_(
                            f"Cannot increase product quantity to {new_qty} as it exceeds available quantity of {max_qty} for material request {material_id.name}.."
                        ))

                    elif quantity_all_purchase == material_line.quantity:
                        material_id.write({'state': 'done'})

        return super().create(vals_list)

    def write(self, vals):
        # Check if material_line_id exists and if product_qty is being updated

        if self.material_line_id and 'product_qty' in vals:
            material_line = self.env['material.request.line'].browse(self.material_line_id.id).exists()

            if material_line:
                material_id = material_line.material_request_id
                domain = [('material_line_id', '=', self.material_line_id.id), ('state', '!=', 'cancel')]
                purchase_lines = self.env['purchase.order.line'].search(domain)
                quantity_old_purchase = sum(purchase_lines.mapped('product_qty'))
                new_qty = vals.get('product_qty')
                quantity_all_purchase = new_qty + quantity_old_purchase - self.product_qty

                if quantity_all_purchase > material_line.quantity:
                    max_qty = material_line.quantity - quantity_old_purchase
                    raise UserError(_(
                        f"Cannot increase product quantity to {new_qty} as it exceeds available quantity of {max_qty} for material request {material_id.name}."
                    ))

                elif quantity_all_purchase == material_line.quantity:
                    material_id.write({'state': 'done'})

        return super().write(vals)


class Stock(models.Model):
    _inherit = 'stock.picking'

    user_request_id = fields.Many2one('res.users', readonly=True)
    ref = fields.Reference([('glass.factory', 'Glass Factory'),
                            ('installations.department', 'Installations Dep'),
                            ('manufacturing.department', 'Manufacturing'),
                            ('operation.department', 'Operation Dep'),
                            ('planning.department', 'Planning Dep'),
                            ('purchase.department', 'Purchase Dep'),
                            ('warehouse.department', 'Warehouse Dep')], readonly=True)
    contract_id = fields.Many2one('contract.contract', readonly=True)
