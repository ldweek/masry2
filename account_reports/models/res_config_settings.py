# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from calendar import monthrange

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import format_date
from odoo.tools import date_utils


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    totals_below_sections = fields.Boolean(related='company_id.totals_below_sections', string='Add totals below sections', readonly=False,
                                           help='When ticked, totals and subtotals appear below the sections of the report.')
    account_tax_periodicity = fields.Selection(related='company_id.account_tax_periodicity', string='Periodicity', readonly=False, required=True)
    account_tax_periodicity_reminder_day = fields.Integer(related='company_id.account_tax_periodicity_reminder_day', string='Reminder', readonly=False, required=True)
    account_tax_periodicity_journal_id = fields.Many2one(related='company_id.account_tax_periodicity_journal_id', string='Journal', readonly=False)

    # Deferred management
    deferred_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Deferred Entries Journal',
        help='Journal used for deferred entries',
        readonly=False,
        related='company_id.deferred_journal_id',
    )
    deferred_expense_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Deferred Expense',
        help='Account used for deferred expenses',
        readonly=False,
        related='company_id.deferred_expense_account_id',
    )
    deferred_revenue_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Deferred Revenue',
        help='Account used for deferred revenues',
        readonly=False,
        related='company_id.deferred_revenue_account_id',
    )
    generate_deferred_expense_entries_method = fields.Selection(
        related='company_id.generate_deferred_expense_entries_method',
        readonly=False, required=True,
        help='Method used to generate deferred expense entries',
    )
    generate_deferred_revenue_entries_method = fields.Selection(
        related='company_id.generate_deferred_revenue_entries_method',
        readonly=False, required=True,
        help='Method used to generate deferred revenue entries',
    )
    deferred_amount_computation_method = fields.Selection(
        related='company_id.deferred_amount_computation_method',
        readonly=False, required=True,
        help='Method used to compute the amount of deferred entries',
    )

    def open_tax_group_list(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tax groups',
            'res_model': 'account.tax.group',
            'view_mode': 'tree',
            'context': {
                'default_country_id': self.account_fiscal_country_id.id,
                'search_default_country_id': self.account_fiscal_country_id.id,
            },
        }
