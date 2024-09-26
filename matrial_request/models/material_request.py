from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class MaterialRequest(models.Model):
    _name = 'material.request'

    name = fields.Char(default='New Material Request')
    user_id = fields.Many2one('res.users', readonly=True, force_save=True)
    employee_id = fields.Many2one('hr.employee')
    date_request = fields.Date(default=fields.Date.today)
    line_ids = fields.One2many('material.request.line', 'material_request_id')
    state = fields.Selection([
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='progress')
    purchase_ids = fields.One2many('purchase.order', compute='get_purchase_ids')
    ref = fields.Reference([('glass.factory', 'Glass Factory'),
                            ('installations.department', 'Installations Dep'),
                            ('manufacturing.department', 'Manufacturing'),
                            ('operation.department', 'Operation Dep'),
                            ('planning.department', 'Planning Dep'),
                            ('purchase.department', 'Purchase Dep'),
                            ('warehouse.department', 'Warehouse Dep')], readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          related='contract_id.analytic_account_id')
    contract_id = fields.Many2one('contract.contract', required=True)
    purchase_count = fields.Integer(compute='compute_count')

    def get_purchase_ids(self):
        for mr in self:
            mr.purchase_ids = self.env['purchase.order'].search([('material_id', '=', mr.id)])

    def compute_count(self):
        for mr in self:
            purchase_lines = self.env['purchase.order.line'].search([('material_line_id', 'in', self.line_ids.ids)])
            mr.purchase_count = self.env['purchase.order'].search_count([('order_line', 'in', purchase_lines.ids)])

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            if not rec.purchase_ids:
                rec.state = 'cancel'
            else:
                raise ValidationError(_('Cannot cancel material request with purchase orders.'))

    @api.model
    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('mr.seq') or _('New')
        return super().create(vals_list)

    def create_po(self):
        self.ensure_one()
        vals = {}
        for mr in self:
            vals = {
                'default_material_id': self.id,
                'default_order_line': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                    'name': line.product_id.name,
                    'product_uom': line.unit_id.id,
                    'contract_id': self.contract_id.id,
                    'analytic_account_id': self.analytic_account_id.id,
                    'material_line_id': line.id,
                }) for line in mr.line_ids],
            }
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'target': 'current',
            'context': vals
        }

    def prepare_po_context(self, records):
        default_po_lines = [
            (0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'name': line.product_id.name,
                'product_uom': line.unit_id.id,
                'contract_id': mr.contract_id.id,
                'analytic_account_id': mr.analytic_account_id.id,
                'material_line_id': mr.id,
            })
            for mr in records
            for line in mr.line_ids
        ]
        return default_po_lines


    def open_purchase_action(self):

        self.ensure_one()
        action = {
            'name': _("Purchase list"),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'context': {'create': False},
        }
        purchase_lines = self.env['purchase.order.line'].search([('material_line_id', 'in', self.line_ids.ids)])
        purchase_id = self.env['purchase.order'].search([('order_line', 'in', purchase_lines.ids)])

        if len(purchase_id) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': purchase_id.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', purchase_id.ids)],
            })
        return action


class MaterialRequestLine(models.Model):
    _name = 'material.request.line'

    material_request_id = fields.Many2one('material.request', ondelete='cascade')
    product_id = fields.Many2one('product.product', required=True)
    quantity = fields.Float(required=True)
    unit_id = fields.Many2one('uom.uom', related='product_id.uom_id', store=True)
