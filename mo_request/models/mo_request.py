from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MaterialRequest(models.Model):
    _name = 'manufacturing.request'

    name = fields.Char(default='New Material Request')
    user_request_id = fields.Many2one('res.users', readonly=True, force_save=True)
    employee_id = fields.Many2one('hr.employee')
    product_id = fields.Many2one('product.product')
    product_uom_qty = fields.Float(required=True)
    date_request = fields.Date(default=fields.Date.today)
    state = fields.Selection([
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='progress')
    mrp_ids = fields.One2many('mrp.production', 'request_id')
    ref = fields.Reference([('glass.factory', 'Glass Factory'),
                            ('installations.department', 'Installations Dep'),
                            ('manufacturing.department', 'Manufacturing'),
                            ('operation.department', 'Operation Dep'),
                            ('planning.department', 'Planning Dep'),
                            ('purchase.department', 'Purchase Dep'),
                            ('warehouse.department', 'Warehouse Dep')], readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', readonly=True)
    contract_id = fields.Many2one('contract.contract', required=True)

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
            vals['name'] = self.env['ir.sequence'].next_by_code('mo.seq') or _('New')
        return super().create(vals_list)

    def create_mrp_production(self):
        self.ensure_one()
        vals = {}
        for mr in self:
            model = mr.ref._name
            record_id = mr.id
            ref = '% s,% s' % (model, record_id)
            vals = {
                'default_contract_id': mr.contract_id.id,
                'default_analytic_account_id': mr.analytic_account_id.id,
                'default_product_uom_qty': mr.product_uom_qty,
                'default_product_id': mr.product_id.id,
                'default_ref': ref,
                'default_user_request_id': self.env.user.id,
            }

        return {
            'name': 'Manufacturing Order',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'target': 'current',
            'context': vals
        }
