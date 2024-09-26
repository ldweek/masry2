# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _inherit = ['mail.thread']

    def _get_allowed_employees(self):
        user = self.env.user
        domain = ['|', ('user_id', '=', user.id), ('parent_id.user_id', '=', user.id)]
        employee_ids = self.env['hr.employee'].search_read(domain, ['id'])
        ids = [rec['id'] for rec in employee_ids]
        return [('id', 'in', ids)]

    name = fields.Char(string='Name', default='Draft')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('approved', 'Approved'),
        ('received', 'Received'),
    ], default='draft', tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', domain=_get_allowed_employees)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string="Department")
    manager_id = fields.Many2one('hr.employee', related='employee_id.parent_id', string="Manager")
    request_line_ids = fields.One2many('purchase.request.line', 'po_request_id')
    show_confirm = fields.Boolean(compute="_compute_show_confirm")
    show_approve = fields.Boolean(compute="_compute_show_approve")
    show_receive = fields.Boolean(compute="_compute_show_receive")
    order_id = fields.Many2one('purchase.order', compute="_compute_order_id")

    # ////////////////////////////////////////////////////////// Model Methods ///////////////////////////////////////////////////////////////////////

    # ////////////////////////////////////////////////////////// Compute Methods /////////////////////////////////////////////////////////////////////

    @api.depends('employee_id')
    def _compute_show_confirm(self):
        for request in self:
            if request.state == 'draft' and request.employee_id:
                if request.employee_id.user_id == self.env.user or request.employee_id.parent_id.user_id == self.env.user:
                    request.show_confirm = True
                else:
                    request.show_confirm = False
            else:
                request.show_confirm = False

    @api.depends('state')
    def _compute_show_approve(self):
        for request in self:
            if request.state == 'confirm':
                if request.employee_id.parent_id.user_id == self.env.user:
                    request.show_approve = True
                else:
                    request.show_approve = False
            else:
                request.show_approve = False

    @api.depends('state')
    def _compute_show_receive(self):
        for request in self:
            if request.state == 'approved':
                manager_ids = self.env.ref('sysgates_purchase_request.purchase_requests_manager').users
                if self.env.user in manager_ids:
                    request.show_receive = True
                else:
                    request.show_receive = False
            else:
                request.show_receive = False

    def _compute_order_id(self):
        for request in self:
            order_id = request.env['purchase.order'].search([('request_id', '=', request.id)])
            if order_id:
                request.order_id = order_id.id
            else:
                request.order_id = False

    # ////////////////////////////////////////////////////////// Handler Methods /////////////////////////////////////////////////////////////////////

    def action_confirm(self):
        self.state = 'confirm'
        self.name = self.env['ir.sequence'].next_by_code('po.request') if self.name == 'Draft' else self.name

    def action_reset_to_draft(self):
        self.state = 'draft'

    def action_approve(self):
        self.state = 'approved'

    def action_receive(self):
        self.state = 'received'

    def action_create_po(self):
        return {
            'name': _('Create Purchase Order'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'view_id': self.env.ref('purchase.purchase_order_form').id,
            'context': self._get_purchase_action_context(),
        }

    def action_view_po(self):
        result = {
            "name": _("Purchase Order"),
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "domain": [('id', "=", self.order_id.id)],
            'view_mode': 'form',
            'res_id': self.order_id.id,
        }
        return result

    def _get_purchase_action_context(self):
        vals = []
        for line in self.request_line_ids:
            vals.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.quantity,
                'product_uom': line.uom_id.id,
                'company_id': self.env.company.id,
            }))

        ctx = {
            'default_request_id': self.id,
            'default_order_line': vals,
        }
        return ctx
