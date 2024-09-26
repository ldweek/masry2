import logging
import re
from email.policy import default

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Contract(models.Model):
    _name = 'contract.contract'
    _order = 'name desc, id desc'

    name = fields.Char()
    start_date = fields.Date(default=fields.Date.context_today)
    contract_date = fields.Date(default=fields.Date.context_today)
    project_name = fields.Char()
    Subject_contract = fields.Text()

    # the first party
    legal_rep = fields.Many2one('hr.employee', string="Legal Rep")
    tech_eng = fields.Many2one('hr.employee', string="Technical Eng")
    executive_eng = fields.Many2one('hr.employee', string="Inspection Eng")

    # the second party
    partner_id = fields.Many2one('res.partner', string='Customer')
    partner_phone = fields.Char(string='Partner Phone', related='partner_id.phone', readonly=False)
    legal_rep_sp = fields.Char(string="Legal Rep Second Party")
    lrp_sp_phone = fields.Char(string="LRP SP Phone")
    address_implementation = fields.Char(string="Implementation Address")
    address_legal_Corresponding = fields.Char(string="LRP SP Address")

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, store=True,
        default=lambda self: self.env.company)
    state = fields.Selection([('draft', 'Draft'),
                              ('executive_inspection', 'Executive inspection'),
                              ('payment_70', 'Payment 70%'),
                              ('technical_operation', 'Technical & Operation'),
                              ('supply_payment_25', 'Supply & Payment 25%'),
                              ('installation_payment_5', 'Installation & Payment 5%'),
                              ('business_stopping', 'Stopping Business'),
                              ('business_resume', 'Business resume'),
                              ('cancel', 'Cancel'), ],
                             string="State", default='draft', tracking=True)

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_currency_id',
        store=True,
        precompute=True,
        ondelete='restrict'
    )
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    locked = fields.Boolean(default=False, copy=False)
    has_active_pricelist = fields.Boolean(
        compute='_compute_has_active_pricelist')
    show_update_pricelist = fields.Boolean(
        string="Has Pricelist Changed", store=False)
    note = fields.Html(
        string="Terms and conditions", readonly=False)

    # departments of contracts
    technical_office_ids = fields.One2many('technical.office', 'contract_id', copy=True)
    glass_factory_ids = fields.One2many('glass.factory', 'contract_id')
    installation_ids = fields.One2many('installations.department', 'contract_id')
    manufacturing_ids = fields.One2many('manufacturing.department', 'contract_id')
    operation_ids = fields.One2many('operation.department', 'contract_id')
    planning_ids = fields.One2many('planning.department', 'contract_id')
    purchasing_ids = fields.One2many('purchase.department', 'contract_id')
    warehouse_ids = fields.One2many('warehouse.department', 'contract_id')

    # count the number of smart buttons
    invoice_count = fields.Integer(compute='_compute_counts')
    purchase_order_count = fields.Integer(compute='_compute_counts')
    sale_order_count = fields.Integer(compute='_compute_counts')
    purchase_order_rep_count = fields.Integer(compute='_compute_counts')
    mrp_order_count = fields.Integer(compute='_compute_counts')
    payment_count = fields.Integer(compute='_compute_counts')
    project_count = fields.Integer(compute='_compute_counts')
    task_count = fields.Integer(compute='_compute_counts')
    opportunity_id = fields.Many2one('crm.lead')

    # commission for employees fields
    inspections_Manager = fields.Many2one('hr.employee', string='Inspections Manager')
    technical_office_manager = fields.Many2one('hr.employee', string='Technical Manager')
    external_commission_id = fields.Many2one('res.partner', string='External commission')
    employee_id = fields.Many2one('hr.employee', string='Telesales')

    # department fields
    dep_tech_eng_id = fields.Many2one('hr.department', string='Department', related='tech_eng.department_id')
    dep_executive_eng_id = fields.Many2one('hr.department', string='Department', related='executive_eng.department_id')
    dep_inspections_manager = fields.Many2one('hr.department', string='Department',
                                              related='inspections_Manager.department_id')
    dep_technical_office_manager = fields.Many2one('hr.department', string='Department',
                                                   related='technical_office_manager.department_id')

    is_tax = fields.Boolean()
    tax_details_binary = fields.Binary(attachment=True)

    # commission Percentage fields
    tech_commission = fields.Float()
    executive_commission = fields.Float()
    external_commission = fields.Float()
    executive_manager_commission = fields.Float()
    tech_manager_commission = fields.Float()

    national_id = fields.Char(string="ID", size=14)

    @api.constrains('national_id')
    def len_number_phone(self):
        for rec in self:
            if rec.national_id:
                if not rec.national_id.isdigit() or len(rec.national_id) != 14:
                    print(rec.national_id.isdigit(), rec.national_id)
                    raise ValidationError('The ID must consist of 14 digits and contain no letters.')

    # amount commission fields
    def check_amount_invoices(self):
        domain = [("contract_id", "=", self.id), ('move_type', 'in', ('out_invoice', 'out_refund'))]
        invoice = self.env['account.move'].search(domain).filtered(lambda inv: inv.state == 'posted')
        if len(invoice) == 0:
            raise UserError(_('No Invoice Posted is available!'))
        total_amount = sum(invoice.mapped('amount_total_signed'))
        if total_amount == 0:
            raise UserError(_('No Amount to get commission!'))
        return total_amount

    def get_commission(self):
        amount = self.check_amount_invoices()

        commission_params = {
            'tech_eng': ('tech_commission', 'tech_commission'),
            'executive_eng': ('inspection_commission', 'executive_commission'),
            'external_commission_id': ('out_commission', 'external_commission'),
            'inspections_Manager': ('inspection_manger_commission', 'executive_manager_commission'),
            'technical_office_manager': ('tech_manger_commission', 'tech_manager_commission')
        }

        for role, (param, field) in commission_params.items():
            if getattr(self, role):
                rate = float(self.env['ir.config_parameter'].sudo().get_param(param, 0))
                if rate != 0:
                    setattr(self, field, rate * amount / 100)

    def _compute_counts(self):
        for record in self:
            record.invoice_count = self.env['account.move'].search_count([('contract_id', '=', record.id)])
            purchase_order_line = self.env['purchase.order.line'].search([('contract_id', '=', record.id)])
            record.purchase_order_count = self.env['purchase.order'].search_count(
                [('is_replacement', '=', False), ('order_line', 'in', purchase_order_line.ids)])
            record.sale_order_count = self.env['sale.order'].search_count(
                [('contract_id', '=', record.id)])
            record.purchase_order_rep_count = self.env['purchase.order'].search_count(
                [('is_replacement', '=', True), ('contract_id', '=', record.id)])
            record.mrp_order_count = self.env['mrp.production'].search_count([('contract_id', '=', record.id)])
            record.payment_count = self.env['account.payment'].search_count([('contract_id', '=', record.id)])
            record.project_count = self.env['project.project'].search_count([('contract_id', '=', record.id)])
            record.task_count = self.env['project.task'].search_count([('contract_id', '=', record.id)])

    def open_sale_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('sale.act_res_partner_2_sale_order')
        action["domain"] = [("contract_id", "=", self.id)]
        action["context"] = {
            'contract_id': self.id,
            'default_contract_id': self.id,
            'default_analytic_account_id': self.analytic_account_id.id,
            'default_partner_id': self.partner_id.id
        }
        return action

    def open_purchase_replacement_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('purchase.act_res_partner_2_purchase_order')
        action["domain"] = [('is_replacement', '=', True), ("contract_id", "=", self.id)]
        action["context"] = {
            'contract_id': self.id,
            'default_contract_id': self.id,
            'default_analytic_account_id': self.analytic_account_id.id,
            'default_is_replacement': True,
            'is_replacement': True,
        }
        return action

    def open_purchase_replacement(self):
        self.ensure_one()
        return {
            'name': _('Purchase Order Rep'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'target': 'current',
            'context': {
                'contract_id': self.id,
                'default_contract_id': self.id,
                'default_analytic_account_id': self.analytic_account_id.id,
                'default_is_replacement': True,
                'is_replacement': True,
            }
        }

    def open_purchase_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('purchase.act_res_partner_2_purchase_order')
        action["domain"] = [("contract_id", "=", self.id), ('is_replacement', '=', False)]
        action["context"] = {'default_contract_id': self.id, 'contract_id': self.id,
                             'default_partner_id': self.partner_id.id,
                             'default_analytic_account_id': self.analytic_account_id.id, }
        return action

    def open_mrp_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('mrp.action_picking_tree_mrp_operation')
        action["domain"] = [("contract_id", "=", self.id)]
        action["context"] = {'default_contract_id': self.id,
                             'default_analytic_account_id': self.analytic_account_id.id, }
        return action

    def open_payment_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_account_all_payments')
        action["domain"] = [("contract_id", "=", self.id)]
        action["context"] = {'default_contract_id': self.id,
                             'default_partner_id': self.partner_id.id,
                             'default_analytic_account_id': self.analytic_account_id.id, }

        return action

    def open_invoices_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('green_contracts.action_move_out_invoice_type_id')
        action["domain"] = [("contract_id", "=", self.id), ('move_type', 'in', ('out_invoice', 'out_refund'))]
        action["context"] = {'default_contract_id': self.id,
                             'default_partner_id': self.partner_id.id,
                             'default_analytic_account_id': self.analytic_account_id.id,
                             'default_move_type': 'out_invoice'}
        return action

    def open_tasks_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('project.action_view_all_task')
        action["domain"] = [("contract_id", "=", self.id)]
        action["context"] = {'default_contract_id': self.id,
                             'default_analytic_account_id': self.analytic_account_id.id, }
        return action

    def open_project_action(self):
        action = self.env['ir.actions.act_window']._for_xml_id('project.open_view_project_all_config')
        action["domain"] = [("contract_id", "=", self.id)]
        action["context"] = {"create": True,
                             'default_contract_id': self.id,
                             'default_partner_id': self.partner_id.id,
                             'default_analytic_account_id': self.analytic_account_id.id, }
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('contract.seq') or _('New')
            analytic_account_id = self.env['account.analytic.account'].create({'name': vals['name'], 'plan_id': 1})
            vals['analytic_account_id'] = analytic_account_id.id

        return super().create(vals_list)

    @api.depends('company_id')
    def _compute_has_active_pricelist(self):
        for order in self:
            order.has_active_pricelist = bool(self.env['product.pricelist'].search(
                [('company_id', 'in', (False, order.company_id.id)), ('active', '=', True)],
                limit=1,
            ))

    @api.depends('state')
    def _compute_locked(self):
        for contract in self:
            contract.locked = contract.state == 'locked'

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Pricelist",
        compute='_compute_pricelist_id',
        store=True, readonly=False, precompute=True, check_company=True,  # Unrequired company
        tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="If you change the pricelist, only newly added lines will be affected.")

    @api.depends('pricelist_id', 'company_id')
    def _compute_currency_id(self):
        for order in self:
            order.currency_id = order.pricelist_id.currency_id or order.company_id.currency_id

    @api.depends('pricelist_id', 'company_id')
    def _compute_currency_id(self):
        for contract in self:
            contract.currency_id = contract.pricelist_id.currency_id or contract.company_id.currency_id

    def _get_lang(self):
        self.ensure_one()

        if self.partner_id.lang and not self.partner_id.is_public:
            return self.partner_id.lang

        return self.env.lang

    @api.depends('partner_id', 'company_id')
    def _compute_pricelist_id(self):
        for order in self:
            if order.state != 'draft':
                continue
            if not order.partner_id:
                order.pricelist_id = False
                continue
            order = order.with_company(order.company_id)
            order.pricelist_id = order.partner_id.property_product_pricelist

    def action_confirm(self):
        for contract in self:
            contract.state = 'confirmed'

    def action_unlock(self):
        for contract in self:
            contract.state = 'confirmed'

    def action_draft(self):
        for contract in self:
            contract.state = 'draft'

    def action_cancel(self):
        for contract in self:
            contract.state = 'cancel'

    def action_view_test(self):
        pass

    def action_distribution_for_departments(self):
        pass

    def vals_for_departments(self, line):
        return {
            'product_id': line.product_id.id,
            'product_uom_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'contract_id': self.id,
            'analytic_account_id': self.analytic_account_id.id,
            'tech_office_line_id': line.id

        }

    def do_distribution_to_departments(self):
        for line in self.technical_office_ids:
            if line.distribution and not line.is_distributed:
                _logger.info('line.distribution: %s', line.distribution)
                model = line.distribution

                if self.env['ir.model'].search([('model', '=', model)]):
                    vals = self.vals_for_departments(line)
                    res = self.env[model].create(vals)
                    line.write({'is_distributed': True})
                else:
                    _logger.warning('No model found for distribution: %s', model)
