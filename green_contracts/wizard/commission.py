from odoo import fields, models, api


class CommissionWizard(models.TransientModel):
    _name = 'commission.wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    employee_id = fields.Many2one('hr.employee')
    rate = fields.Float(compute='_get_rate')
    total_amount = fields.Float(compute='_compute_total_amount')
    commission_amount = fields.Float(compute='compute_commission_amount')
    invoice_line_ids = fields.One2many('account.move.line', compute='get_invoice_line_ids')

    @api.onchange('total_amount')
    def _get_rate(self):
        self.rate = 0.0
        if self.total_amount:
            if 700000 <= self.total_amount <= 1000000:
                self.rate = self.env['ir.config_parameter'].sudo().get_param('first_rate_commission')
            elif 1000001 <= self.total_amount <= 1500000:
                self.rate = self.env['ir.config_parameter'].sudo().get_param('second_rate_commission')
            elif 1500001 <= self.total_amount <= 2000000:
                self.rate = self.env['ir.config_parameter'].sudo().get_param('third_rate_commission')
            elif 2000001 <= self.total_amount <= 2500000:
                self.rate = self.env['ir.config_parameter'].sudo().get_param('four_rate_commission')
            elif self.total_amount > 2500000:
                self.rate = self.env['ir.config_parameter'].sudo().get_param('five_rate_commission')

    @api.onchange('date_from', 'date_to', 'employee_id')
    def get_invoice_line_ids(self):
        if self.date_from and self.date_to and self.employee_id:
            contract_ids = self.env['contract.contract'].search(
                ['|', '|', '|', '|', '|', ('inspections_Manager', '=', self.employee_id.id),
                  ('technical_office_manager', '=', self.employee_id.id),
                  ('external_commission_id', '=', self.employee_id.id),
                  ('tech_eng', '=', self.employee_id.id),
                  ('executive_eng', '=', self.employee_id.id),
                  ('employee_id', '=', self.employee_id.id) ]).ids
            print('contract_ids==>', contract_ids)

            domain = [
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('contract_id', 'in', contract_ids),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('parent_state', '=', 'posted'),
                ('product_id', '!=', False),
                ('contract_id', '!=', False),
            ]
            move_lines = self.env['account.move.line'].search(domain, order='date asc')
            self.invoice_line_ids = move_lines.ids
        else:
            self.invoice_line_ids = False

    @api.onchange('invoice_line_ids')
    def _compute_total_amount(self):
        self.total_amount = 0.0
        if self.invoice_line_ids:
            self.total_amount = sum(self.invoice_line_ids.mapped('total_amount_co'))
            print(self.invoice_line_ids.mapped('total_amount_co'))

    @api.onchange('rate', 'total_amount')
    def compute_commission_amount(self):
        self.commission_amount = 0.0
        if self.rate and self.total_amount:
            self.commission_amount = self.total_amount * self.rate / 100.0


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    total_amount_co = fields.Float(compute='get_amount_for_commission')

    @api.depends('price_total', 'move_type', 'product_id')
    def get_amount_for_commission(self):
        for rec in self:
            if rec.move_type == 'out_invoice':
                rec.total_amount_co = rec.price_subtotal
            elif rec.move_type == 'out_refund':
                rec.total_amount_co = -rec.price_subtotal
            else:
                rec.total_amount_co = 0.0
