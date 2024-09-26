from odoo import models, fields


class Contract(models.Model):
    _inherit = 'contract.contract'

    employee_id = fields.Many2one('hr.employee', string='Telesales',
                                  related='opportunity_id.employee_id', store=True)
    dep_employee_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id')
    telesales_commission = fields.Float()

    def get_commission(self):
        amount = self.check_amount_invoices()

        commission_params = {
            'tech_eng': ('tech_commission', 'tech_commission'),
            'executive_eng': ('inspection_commission', 'executive_commission'),
            'external_commission_id': ('out_commission', 'external_commission'),
            'inspections_Manager': ('inspection_manger_commission', 'executive_manager_commission'),
            'technical_office_manager': ('tech_manger_commission', 'tech_manager_commission'),
            'employee_id': ('telesales_commission', 'telesales_commission'),
        }
        for role, (param, field) in commission_params.items():
            if getattr(self, role):
                rate = float(self.env['ir.config_parameter'].sudo().get_param(param, 0))
                if rate != 0:
                    setattr(self, field, rate * amount / 100)
