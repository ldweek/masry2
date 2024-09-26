from odoo import models, fields, api


class FormContracts(models.Model):
    _name = 'form.contracts'

    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    contract_id = fields.Many2one('contract.contract', string='Contract')
    date = fields.Date(default=lambda self: fields.Date.context_today(self))
    contract_date = fields.Date()
    start_date = fields.Date()

    def print_contract_form(self):
        return self.env.ref('ad_form_contract.form_contract_print_pdf').report_action(self, data=None)
