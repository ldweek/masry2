from odoo import fields, models, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    contract_id = fields.Many2one('contract.contract')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_id = fields.Many2one('contract.contract', compute="get_contract_id", store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=True)

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        res['contract_id'] = self.contract_id.id
        res['analytic_account_id'] = self.analytic_account_id.id
        return res

    @api.depends('opportunity_id', 'opportunity_id.contract_id')
    def get_contract_id(self):
        for record in self.filtered(lambda r: not r.contract_id and r.opportunity_id):
            record.contract_id = record.opportunity_id.contract_id


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    contract_id = fields.Many2one('contract.contract', compute='_get_contract_and_analytic_account', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          related='contract_id.analytic_account_id')
    material_line_id = fields.Many2one('material.request.line')

    @api.depends('order_id', 'product_id', 'order_id.contract_id')
    @api.onchange('product_id')
    def _get_contract_and_analytic_account(self):
        for line in self:
            if not line.contract_id:
                line.contract_id = line.order_id.contract_id.id if line.order_id and line.order_id.contract_id else None

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = super()._prepare_invoice_line(**optional_values)
        res['contract_id'] = self.contract_id.id
        res['analytic_account_id'] = self.analytic_account_id.id
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    contract_id = fields.Many2one('contract.contract', )
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=True)
    is_replacement = fields.Boolean(default=False)

    @api.model_create_multi
    def create(self, vals_list):
        ctx = self._context
        for vals in vals_list:
            if ctx.get('is_replacement'):
                vals['name'] = self.env['ir.sequence'].next_by_code('Purchase.order.replacement') or _('New')
        return super().create(vals_list)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    contract_id = fields.Many2one('contract.contract', compute='_get_contract_and_analytic_account', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          related='contract_id.analytic_account_id')
    material_line_id = fields.Many2one('material.request.line')
    error_responsible_id = fields.Many2one('hr.employee')
    is_deduction = fields.Boolean()

    @api.depends('order_id', 'product_id')
    @api.onchange('product_id')
    def _get_contract_and_analytic_account(self):
        for line in self:
            if not line.contract_id:
                line.contract_id = line.order_id.contract_id.id if line.order_id and line.order_id.contract_id else None
            if not line.analytic_account_id:
                line.analytic_account_id = line.order_id.analytic_account_id.id if line.order_id and line.order_id.analytic_account_id else None

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super()._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        res['contract_id'] = self.contract_id.id if self.contract_id else None
        return res

    def deduction_salary_action(self):
        # check if multi employee raise errors
        list_of_employees = set(self.mapped('error_responsible_id').mapped('id'))
        if len(list_of_employees) > 1:
            raise UserError(_('Cannot deduct salary for multiple employees. Please select only one employee.'))

        employee_id = list(list_of_employees)[0]

        # deduct salary for employee
        total_deduction = sum(self.mapped('price_subtotal'))
        limit_allowance = self.env['ir.config_parameter'].sudo().get_param('limit_error')
        net_deduction = float(total_deduction) - float(limit_allowance)

        if net_deduction > 0:
            vals = {
                'employee_id': employee_id,
                'penalty_type': 'amount',
                'penalty_amount': net_deduction,
            }

            res = self.env['penalty.request'].create(vals)
            return {
                'type': 'ir.actions.act_window',
                'name': _('Create Penalty Request'),
                'view_mode': 'form',
                'res_model': 'penalty.request',
                'res_id': res.id,
                'target': 'current',
            }
        else:
            raise UserError(_('No need to deduct salary. The total deduction is within the limit.'))


class Mrp(models.Model):
    _inherit = 'mrp.production'

    contract_id = fields.Many2one('contract.contract', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=True)

    ref = fields.Reference([('glass.factory', 'Glass Factory'),
                            ('installations.department', 'Installations Dep'),
                            ('manufacturing.department', 'Manufacturing'),
                            ('operation.department', 'Operation Dep'),
                            ('planning.department', 'Planning Dep'),
                            ('purchase.department', 'Purchase Dep'),
                            ('warehouse.department', 'Warehouse Dep')], readonly=True)
    user_request_id = fields.Many2one('res.users', readonly=True)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    contract_id = fields.Many2one('contract.contract')
    analytic_account_id = fields.Many2one('account.analytic.account', related='contract_id.analytic_account_id',
                                          copy=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('payment_type') == 'outbound':
                vals['analytic_account_id'] = False
                vals['contract_id'] = False
        return super().create(vals_list)


class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_id = fields.Many2one('contract.contract')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=True)
    deferred_move_ids = fields.Many2many(
        string="Deferred Entries",
        comodel_name='account.move',
        relation='account_move_deferred_rel',
        column1='original_move_id',
        column2='deferred_move_id',
        help="The deferred entries created by this invoice",
        copy=False,
    )

    def action_register_payment(self):
        res = super().action_register_payment()
        res['context'].update({'default_contract_id': self.contract_id.id,
                               'default_analytic_account_id': self.analytic_account_id.id})
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    contract_id = fields.Many2one('contract.contract', compute='_get_contract_and_analytic_account', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          compute='_get_contract_and_analytic_account')
    material_line_id = fields.Many2one('material.request.line')

    @api.depends('move_id', 'product_id')
    @api.onchange('product_id')
    def _get_contract_and_analytic_account(self):
        for line in self:
            if not line.contract_id:
                line.contract_id = line.move_id.contract_id.id if line.move_id and line.move_id.contract_id else None
            if not line.analytic_account_id:
                line.analytic_account_id = line.move_id.analytic_account_id.id if line.move_id and line.move_id.analytic_account_id else None


class Project(models.Model):
    _inherit = 'project.project'

    contract_id = fields.Many2one('contract.contract', compute='_get_contract_id', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', related='contract_id.analytic_account_id',
                                          string='Analytic Account', copy=True)

    @api.depends('sale_order_id.contract_id', 'sale_line_id', 'sale_order_id', 'sale_line_id.contract_id')
    def _get_contract_id(self):
        for record in self.filtered(lambda r: not r.contract_id):
            record.contract_id = False
            all_sale_orders = record._fetch_sale_order_items(
                {'project.task': [('state', 'in', self.env['project.task'].OPEN_STATES)]}).sudo().order_id
            if all_sale_orders:
                record.contract_id = all_sale_orders.contract_id
            elif record.sale_order_id:
                record.contract_id = record.sale_order_id.contract_id


class ProjectTask(models.Model):
    _inherit = 'project.task'

    contract_id = fields.Many2one('contract.contract', compute='_get_contract_id', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                          related='contract_id.analytic_account_id', )

    @api.depends('sale_line_id', 'sale_line_id.contract_id')
    def _get_contract_id(self):
        for record in self.filtered(lambda r: not r.contract_id):
            record.contract_id = False
            if record.sale_line_id:
                record.contract_id = record.sale_line_id.contract_id.id


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    user_request_id = fields.Many2one('res.users', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=True)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    contract_id = fields.Many2one('contract.contract')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')


class StockMove(models.Model):
    _inherit = 'stock.move'

    contract_id = fields.Many2one('contract.contract')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.depends('picking_id', 'product_id')
    @api.onchange('product_id')
    def _get_contract_and_analytic_account(self):
        for line in self:
            if not line.contract_id:
                line.contract_id = line.picking_id.contract_id.id if line.picking_id and line.picking_id.contract_id else None
            if not line.analytic_account_id:
                line.analytic_account_id = line.picking_id.analytic_account_id.id if line.picking_id and line.picking_id.analytic_account_id else None

    @api.model_create_multi
    def create(self, vals_list):
        ctx = self._context
        for vals in vals_list:
            if ctx.get('contract_id'):
                vals['contract_id'] = ctx['contract_id']
            if ctx.get('analytic_account_id'):
                vals['analytic_account_id'] = ctx['analytic_account_id']
        return super().create(vals_list)
