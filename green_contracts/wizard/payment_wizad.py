from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    contract_id = fields.Many2one('contract.contract')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    def _create_payment_vals_from_batch(self, batch_result):
        res = super()._create_payment_vals_from_batch(batch_result)
        context = self.env.context
        res['contract_id'] = self.contract_id.id
        res['analytic_account_id'] = self.analytic_account_id.id
        return res
