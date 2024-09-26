# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import frozendict, SQL
from dateutil.relativedelta import relativedelta


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"

    expected_pay_date = fields.Date('Expected Date',
                                    help="Expected payment date as manually set through the customer statement"
                                         "(e.g: if you had the customer on the phone and want to remember the date he promised he would pay)")

    @api.constrains('tax_ids', 'tax_tag_ids')
    def _check_taxes_on_closing_entries(self):
        for aml in self:
            if aml.move_id.tax_closing_end_date and (aml.tax_ids or aml.tax_tag_ids):
                raise UserError(_("You cannot add taxes on a tax closing move line."))

    move_attachment_ids = fields.One2many('ir.attachment', compute='_compute_attachment')

    # Deferred management fields
    deferred_start_date = fields.Date(
        string="Start Date",
        compute='_compute_deferred_start_date', store=True, readonly=False,
        index='btree_not_null',
        copy=False,
        help="Date at which the deferred expense/revenue starts"
    )
    deferred_end_date = fields.Date(
        string="End Date",
        index='btree_not_null',
        copy=False,
        help="Date at which the deferred expense/revenue ends"
    )
    has_deferred_moves = fields.Boolean(compute='_compute_has_deferred_moves')

    def _order_to_sql(self, order, query, alias=None, reverse=False):
        sql_order = super()._order_to_sql(order, query, alias, reverse)
        preferred_aml_residual_value = self._context.get('preferred_aml_value')
        preferred_aml_currency_id = self._context.get('preferred_aml_currency_id')
        if preferred_aml_residual_value and preferred_aml_currency_id and order == self._order:
            currency = self.env['res.currency'].browse(preferred_aml_currency_id)
            # using round since currency.round(55.55) = 55.550000000000004
            preferred_aml_residual_value = round(preferred_aml_residual_value, currency.decimal_places)
            sql_residual_currency = self._field_to_sql(alias or self._table, 'amount_residual_currency', query)
            sql_currency = self._field_to_sql(alias or self._table, 'currency_id', query)
            return SQL(
                "ROUND(%(residual_currency)s, %(decimal_places)s) = %(value)s "
                "AND %(currency)s = %(currency_id)s DESC, %(order)s",
                residual_currency=sql_residual_currency,
                decimal_places=currency.decimal_places,
                value=preferred_aml_residual_value,
                currency=sql_currency,
                currency_id=currency.id,
                order=sql_order,
            )
        return sql_order

    def copy_data(self, default=None):
        data_list = super().copy_data(default=default)
        for line, values in zip(self, data_list):
            if 'move_reverse_cancel' in self._context:
                values['deferred_start_date'] = line.deferred_start_date
                values['deferred_end_date'] = line.deferred_end_date
        return data_list

    def write(self, vals):
        """ Prevent changing the account of a move line when there are already deferral entries.
        """
        if 'account_id' in vals:
            for line in self:
                if (
                        line.has_deferred_moves
                        and line.deferred_start_date
                        and line.deferred_end_date
                        and vals['account_id'] != line.account_id.id
                ):
                    raise UserError(_(
                        "You cannot change the account for a deferred line in %(move_name)s if it has already been deferred.",
                        move_name=line.move_id.display_name
                    ))
        return super().write(vals)

    # ============================= START - Deferred management ====================================
    def _compute_has_deferred_moves(self):
        for line in self:
            line.has_deferred_moves = line.move_id.deferred_move_ids

    def _is_compatible_account(self):
        self.ensure_one()
        return (
                self.move_id.is_purchase_document()
                and
                self.account_id.account_type in ('expense', 'expense_depreciation', 'expense_direct_cost')
        ) or (
                self.move_id.is_sale_document()
                and
                self.account_id.account_type in ('income', 'income_other')
        )

    @api.onchange('deferred_start_date')
    def _onchange_deferred_start_date(self):
        if not self._is_compatible_account():
            self.deferred_start_date = False

    @api.onchange('deferred_end_date')
    def _onchange_deferred_end_date(self):
        if not self._is_compatible_account():
            self.deferred_end_date = False

    @api.depends('deferred_end_date', 'move_id.invoice_date', 'move_id.state')
    def _compute_deferred_start_date(self):
        for line in self:
            if not line.deferred_start_date and line.move_id.invoice_date and line.deferred_end_date:
                line.deferred_start_date = line.move_id.invoice_date

    @api.constrains('deferred_start_date', 'deferred_end_date', 'account_id')
    def _check_deferred_dates(self):
        for line in self:
            if line.deferred_start_date and not line.deferred_end_date:
                raise UserError(_("You cannot create a deferred entry with a start date but no end date."))
            elif line.deferred_start_date and line.deferred_end_date and line.deferred_start_date > line.deferred_end_date:
                raise UserError(_("You cannot create a deferred entry with a start date later than the end date."))

    @api.model
    def _get_deferred_tax_key(self, line, tax_key, tax_repartition_line_id):
        if (
                line.deferred_start_date
                and line.deferred_end_date
                and line._is_compatible_account()
                and tax_repartition_line_id
                and not tax_repartition_line_id.use_in_tax_closing
        ):
            return frozendict(
                **tax_key,
                deferred_start_date=line.deferred_start_date,
                deferred_end_date=line.deferred_end_date,
            )
        return tax_key

    @api.depends('deferred_start_date', 'deferred_end_date')
    def _compute_tax_key(self):
        super()._compute_tax_key()
        for line in self:
            line.tax_key = self._get_deferred_tax_key(line, line.tax_key, line.tax_repartition_line_id)

    @api.depends('deferred_start_date', 'deferred_end_date')
    def _compute_all_tax(self):
        super()._compute_all_tax()
        for line in self:
            for key in list(line.compute_all_tax.keys()):
                tax_repartition_line_id = self.env['account.tax.repartition.line'].browse(key.get('tax_repartition_line_id'))
                new_key = self._get_deferred_tax_key(line, key, tax_repartition_line_id)
                line.compute_all_tax[new_key] = line.compute_all_tax.pop(key)

    @api.model
    def _get_deferred_ends_of_month(self, start_date, end_date):
        """
        :return: a list of dates corresponding to the end of each month between start_date and end_date.
            See test_get_ends_of_month for examples.
        """
        dates = []
        while start_date <= end_date:
            start_date = start_date + relativedelta(day=31)  # Go to end of month
            dates.append(start_date)
            start_date = start_date + relativedelta(days=1)  # Go to first day of next month
        return dates

    def _get_deferred_periods(self):
        """
        :return: a list of tuples (start_date, end_date) during which the deferred expense/revenue is spread.
            If there is only one period containing the move date, it means that we don't need to defer the
            expense/revenue since the invoice deferral and its deferred entry will be created on the same day and will
            thus cancel each other.
        """
        self.ensure_one()
        periods = [
            (max(self.deferred_start_date, date.replace(day=1)), min(date, self.deferred_end_date), 'current')
            for date in self._get_deferred_ends_of_month(self.deferred_start_date, self.deferred_end_date)
        ]
        if not periods or len(periods) == 1 and periods[0][0].replace(day=1) == self.date.replace(day=1):
            return []
        else:
            return periods

    @api.model
    def _get_deferred_amounts_by_line_values(self, line):
        return {
            'account_id': line['account_id'],
            'balance': line['balance'],
            'move_id': line['move_id'],
        }

    @api.model
    def _get_deferred_lines_values(self, account_id, balance, ref, analytic_distribution, line=None):
        return {
            'account_id': account_id,
            'balance': balance,
            'name': ref,
            'analytic_distribution': analytic_distribution,
        }

    # ============================= END - Deferred management ====================================
