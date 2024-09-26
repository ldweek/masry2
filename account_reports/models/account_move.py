# -*- coding: utf-8 -*-

from odoo import api, models, fields, _, Command
from odoo.exceptions import UserError
from odoo.tools.misc import format_date
from odoo.tools import date_utils

from dateutil.relativedelta import relativedelta
from markupsafe import Markup
import calendar


class AccountMove(models.Model):
    _inherit = "account.move"

    # used for VAT closing, containing the end date of the period this entry closes
    tax_closing_end_date = fields.Date()
    tax_report_control_error = fields.Boolean()  # DEPRECATED; will be removed in master
    # technical field used to know whether to show the tax closing alert or not
    tax_closing_alert = fields.Boolean(compute='_compute_tax_closing_alert')
    # Used to display a warning banner in case the current closing is a main company (of branches or tax unit), as posting it will post other moves
    tax_closing_show_multi_closing_warning = fields.Boolean(compute="_compute_tax_closing_show_multi_closing_warning")

    @api.depends('company_id', 'state')
    def _compute_tax_closing_show_multi_closing_warning(self):
        for move in self:
            move.tax_closing_show_multi_closing_warning = False

            if move.tax_closing_end_date and move.state == 'draft':
                report, options = move._get_report_options_from_tax_closing_entry()
                report_company_ids = report.get_report_company_ids(options)
                sender_company = report._get_sender_company_for_export(options)

                if len(report_company_ids) > 1 and sender_company == move.company_id:
                    other_company_closings = self.env['account.move'].search([
                        ('tax_closing_end_date', '=', move.tax_closing_end_date),
                        ('company_id', 'in', report_company_ids),
                        ('state', '=', 'posted'),
                    ])
                    # Show the warning if some of the sub companies (branches or member of the tax unit) still need to post a tax closing.
                    move.tax_closing_show_multi_closing_warning = len(other_company_closings) != len(report_company_ids) - 1

    def _post(self, soft=True):
        # Overridden to create carryover external values and join the pdf of the report when posting the tax closing
        for move in self.filtered(lambda m: m.tax_closing_end_date):
            report, options = move._get_report_options_from_tax_closing_entry()
            move._close_tax_period(report, options)

        return super()._post(soft)

    def button_draft(self):
        # Overridden in order to delete the carryover values when resetting the tax closing to draft
        super().button_draft()
        for closing_move in self.filtered(lambda m: m.tax_closing_end_date):
            report, options = closing_move._get_report_options_from_tax_closing_entry()
            closing_months_delay = closing_move.company_id._get_tax_periodicity_months_delay()

            carryover_values = self.env['account.report.external.value'].search([
                ('carryover_origin_report_line_id', 'in', report.line_ids.ids),
                ('date', '=', options['date']['date_to']),
            ])

            carryover_impacted_period_end = fields.Date.from_string(options['date']['date_to']) + relativedelta(months=closing_months_delay)
            tax_lock_date = closing_move.company_id.tax_lock_date
            if carryover_values and tax_lock_date and tax_lock_date >= carryover_impacted_period_end:
                raise UserError(_("You cannot reset this closing entry to draft, as it would delete carryover values impacting the tax report of a "
                                  "locked period. To do this, you first need to modify you tax return lock date."))

            carryover_values.unlink()

    def action_open_tax_report(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account_reports.action_account_report_gt")
        if not self.tax_closing_end_date:
            raise UserError(_("You can't open a tax report from a move without a VAT closing date."))
        options = self._get_report_options_from_tax_closing_entry()[1]
        # Pass options in context and set ignore_session: true to prevent using session options
        action.update({'params': {'options': options, 'ignore_session': True}})
        return action

    def _close_tax_period(self, report, options):
        """ Closes tax closing entries. The tax closing activities on them will be marked done, and the next tax closing entry
        will be generated or updated (if already existing). Also, a pdf of the tax report at the time of closing
        will be posted in the chatter of each move.

        The tax lock date of each  move's company will be set to the move's date in case no other draft tax closing
        move exists for that company (whatever their foreign VAT fiscal position) before or at that date, meaning that
        all the tax closings have been performed so far.
        """
        if not self.user_has_groups('account.group_account_manager'):
            raise UserError(_('Only Billing Administrators are allowed to change lock dates!'))

        tax_closing_activity_type = self.env.ref('account_reports.tax_closing_activity_type')

        for move in self:
            # Change lock date to end date of the period, if all other tax closing moves before this one have been treated
            open_previous_closing = self.env['account.move'].search([
                ('activity_ids.activity_type_id', '=', tax_closing_activity_type.id),
                ('company_id', '=', move.company_id.id),
                ('date', '<=', move.date),
                ('state', '=', 'draft'),
                ('id', '!=', move.id),
            ], limit=1)

            if not open_previous_closing and (not move.company_id.tax_lock_date or move.tax_closing_end_date > move.company_id.tax_lock_date):
                move.company_id.sudo().tax_lock_date = move.tax_closing_end_date

            sender_company = report._get_sender_company_for_export(options)
            company_ids = report.get_report_company_ids(options)
            if sender_company == move.company_id:
                # In branch/tax unit setups, first post all the unposted moves of the other companies when posting the main company.
                tax_closing_action = self.env['account.tax.report.handler'].action_periodic_vat_entries(options)
                depending_closings = self.env['account.move'].with_context(allowed_company_ids=company_ids).search([
                    *(tax_closing_action.get('domain') or [('id', '=', tax_closing_action['res_id'])]),
                    ('id', '!=', move.id),
                ])
                depending_closings_to_post = depending_closings.filtered(lambda x: x.state == 'draft')
                if depending_closings_to_post:
                    depending_closings_to_post.action_post()

                # Generate the carryover values.
                report.with_context(allowed_company_ids=company_ids)._generate_carryover_external_values(options)

                # Post the message with the attachments (PDF of the report, and possibly an additional export file)
                attachments = move._get_vat_report_attachments(report, options)
                subject = _(
                    "Vat closing from %s to %s",
                    format_date(self.env, options['date']['date_from']),
                    format_date(self.env, options['date']['date_to']),
                )
                move.with_context(no_new_invoice=True).message_post(body=move.ref, subject=subject, attachments=attachments)

                # Log a note on depending closings, redirecting to the main one
                for closing_move in depending_closings:
                    closing_move.message_post(
                        body=Markup(
                            _("The attachments of the tax report can be found on the <a href='#' data-oe-model='account.move' data-oe-id='%s'>closing entry</a> of the representative company.",
                              move.id)),
                    )

            # End activity
            activity = move.activity_ids.filtered(lambda m: m.activity_type_id.id == tax_closing_activity_type.id)
            if activity:
                activity.action_done()

            # Create the recurring entry (new draft move and new activity)
            if move.fiscal_position_id.foreign_vat:
                next_closing_params = {'fiscal_positions': move.fiscal_position_id}
            else:
                next_closing_params = {'include_domestic': True}
            move.company_id._get_and_update_tax_closing_moves(move.tax_closing_end_date + relativedelta(days=1), **next_closing_params)

    def refresh_tax_entry(self):
        for move in self.filtered(lambda m: m.tax_closing_end_date and m.state == 'draft'):
            report, options = move._get_report_options_from_tax_closing_entry()
            self.env['account.generic.tax.report.handler']._generate_tax_closing_entries(report, options, closing_moves=move)

    def _get_report_options_from_tax_closing_entry(self):
        self.ensure_one()
        date_to = self.tax_closing_end_date
        # Take the periodicity of tax report from the company and compute the starting period date.
        delay = self.company_id._get_tax_periodicity_months_delay() - 1
        date_from = date_utils.start_of(date_to + relativedelta(months=-delay), 'month')

        # In case the company submits its report in different regions, a closing entry
        # is made for each fiscal position defining a foreign VAT.
        # We hence need to make sure to select a tax report in the right country when opening
        # the report (in case there are many, we pick the first one available; it doesn't impact the closing)
        if self.fiscal_position_id.foreign_vat:
            fpos_option = self.fiscal_position_id.id
            report_country = self.fiscal_position_id.country_id
        else:
            fpos_option = 'domestic'
            report_country = self.company_id.account_fiscal_country_id

        generic_tax_report = self.env.ref('account.generic_tax_report')
        tax_report = self.env['account.report'].search([
            ('availability_condition', '=', 'country'),
            ('country_id', '=', report_country.id),
            ('root_report_id', '=', generic_tax_report.id),
        ], limit=1)

        if not tax_report:
            tax_report = generic_tax_report

        options = {
            'date': {
                'date_from': fields.Date.to_string(date_from),
                'date_to': fields.Date.to_string(date_to),
                'filter': 'custom',
                'mode': 'range',
            },
            'fiscal_position': fpos_option,
            'tax_unit': 'company_only',
        }

        if tax_report.filter_multi_company == 'tax_units':
            # Enforce multicompany if the closing is done for a tax unit
            candidate_tax_unit = self.company_id.account_tax_unit_ids.filtered(lambda x: x.country_id == report_country)
            if candidate_tax_unit:
                options['tax_unit'] = candidate_tax_unit.id
                company_ids = candidate_tax_unit.company_ids.ids
            else:
                same_vat_branches = self.env.company._get_branches_with_same_vat()
                # Consider the one with the least number of parents (highest in hierarchy) as the active company, coming first
                company_ids = same_vat_branches.sorted(lambda x: len(x.parent_ids)).ids
        else:
            company_ids = self.env.company.ids

        report_options = tax_report.with_context(allowed_company_ids=company_ids).get_options(previous_options=options)

        return tax_report, report_options

    def _get_vat_report_attachments(self, report, options):
        # Fetch pdf
        pdf_data = report.export_to_pdf(options)
        return [(pdf_data['file_name'], pdf_data['file_content'])]

    def _compute_tax_closing_alert(self):
        for move in self:
            move.tax_closing_alert = (
                    move.state == 'posted'
                    and move.tax_closing_end_date
                    and move.company_id.tax_lock_date
                    and move.company_id.tax_lock_date < move.tax_closing_end_date
            )

    # ============================= START - Deferred Management ====================================

    def _get_deferred_entries_method(self):
        self.ensure_one()
        if self.is_outbound():
            return self.company_id.generate_deferred_expense_entries_method
        return self.company_id.generate_deferred_revenue_entries_method

    @api.depends('deferred_original_move_ids')
    def _compute_deferred_entry_type(self):
        for move in self:
            if move.deferred_original_move_ids:
                move.deferred_entry_type = 'expense' if move.deferred_original_move_ids[0].is_outbound() else 'revenue'
            else:
                move.deferred_entry_type = False

    @api.model
    def _get_deferred_diff_dates(self, start, end):
        """
        Returns the number of months between two dates [start, end[
        The computation is done by using months of 30 days so that the deferred amount for february
        (28-29 days), march (31 days) and april (30 days) are all the same (in case of monthly computation).
        See test_deferred_management_get_diff_dates for examples.
        """
        if start > end:
            start, end = end, start
        nb_months = end.month - start.month + 12 * (end.year - start.year)
        start_day, end_day = start.day, end.day
        if start_day == calendar.monthrange(start.year, start.month)[1]:
            start_day = 30
        if end_day == calendar.monthrange(end.year, end.month)[1]:
            end_day = 30
        nb_days = end_day - start_day
        return (nb_months * 30 + nb_days) / 30

    @api.model
    def _get_deferred_period_amount(self, method, period_start, period_end, line_start, line_end, balance):
        """
        Returns the amount to defer for the given period taking into account the deferred method (day/month).
        """
        if method == 'day':
            amount_per_day = balance / (line_end - line_start).days
            return (period_end - period_start).days * amount_per_day if period_end > line_start else 0
        else:
            amount_per_month = balance / self._get_deferred_diff_dates(line_end, line_start)
            nb_months_period = self._get_deferred_diff_dates(period_end, period_start)
            return nb_months_period * amount_per_month if period_end > line_start and period_end > period_start else 0

    @api.model
    def _get_deferred_amounts_by_line(self, lines, periods):
        """
        :return: a list of dictionaries containing the deferred amounts for each line and each period
        E.g. (where period1 = (date1, date2, label1), period2 = (date2, date3, label2), ...)
        [
            {'account_id': 1, period_1: 100, period_2: 200},
            {'account_id': 1, period_1: 100, period_2: 200},
            {'account_id': 2, period_1: 300, period_2: 400},
        ]
        """
        values = []
        for line in lines:
            line_start = fields.Date.to_date(line['deferred_start_date'])
            line_end = fields.Date.to_date(line['deferred_end_date'])
            if line_end < line_start:
                # This normally shouldn't happen, but if it does, would cause calculation errors later on.
                # To not make the reports crash, we just set both dates to the same day.
                # The user should fix the dates manually.
                line_end = line_start

            columns = {}
            for period in periods:
                if period[2] == 'not_started' and line_start <= period[0]:
                    # The 'Not Started' column only considers lines starting the deferral after the report end date
                    columns[period] = 0.0
                    continue
                # periods = [Total, Not Started, Before, ..., Current, ..., Later]
                # The dates to calculate the amount for the current period
                period_start = max(period[0], line_start)
                period_end = min(period[1], line_end)
                if (
                        period[2] in ('not_started', 'later') and period[0] < line_start
                        or len(periods) <= 1
                        or period[2] not in ('not_started', 'before', 'later')
                ):
                    # We are subtracting 1 day from `period_start` because the start date should be included when:
                    # - in the 'Not Started' or 'Later' period if the deferral has not started yet (line_start, line_end)
                    # - we only have one period
                    # - not in the 'Not Started', 'Before' or 'Later' period
                    period_start -= relativedelta(days=1)
                columns[period] = self._get_deferred_period_amount(
                    self.env.company.deferred_amount_computation_method,
                    period_start, period_end,
                    line_start - relativedelta(days=1), line_end,  # -1 because we want to include the start date
                    line['balance']
                )

            values.append({
                **self.env['account.move.line']._get_deferred_amounts_by_line_values(line),
                **columns,
            })
        return values

    @api.model
    def _get_deferred_lines(self, line, deferred_account, period, ref, force_balance=None):
        """
        :return: a list of Command objects to create the deferred lines of a single given period
        """
        deferred_amounts = self._get_deferred_amounts_by_line(line, [period])[0]
        balance = deferred_amounts[period] if force_balance is None else force_balance
        return [
            Command.create({
                **self.env['account.move.line']._get_deferred_lines_values(account.id, coeff * balance, ref, line.analytic_distribution, line),
                'partner_id': line.partner_id.id,
                'product_id': line.product_id.id,
            })
            for (account, coeff) in [(deferred_amounts['account_id'], 1), (deferred_account, -1)]
        ]

    def _generate_deferred_entries(self):
        """
        Generates the deferred entries for the invoice.
        """
        self.ensure_one()
        if self.is_entry():
            raise UserError(_("You cannot generate deferred entries for a miscellaneous journal entry."))
        assert not self.deferred_move_ids, "The deferred entries have already been generated for this document."
        is_deferred_expense = self.is_purchase_document()
        deferred_account = self.company_id.deferred_expense_account_id if is_deferred_expense else self.company_id.deferred_revenue_account_id
        deferred_journal = self.company_id.deferred_journal_id
        if not deferred_journal:
            raise UserError(_("Please set the deferred journal in the accounting settings."))
        if not deferred_account:
            raise UserError(_("Please set the deferred accounts in the accounting settings."))

        for line in self.line_ids.filtered(lambda l: l.deferred_start_date and l.deferred_end_date):
            periods = line._get_deferred_periods()
            if not periods:
                continue

            ref = _("Deferral of %s", line.move_id.name or '')
            # Defer the current invoice
            move_fully_deferred = self.create({
                'move_type': 'entry',
                'deferred_original_move_ids': [Command.set(line.move_id.ids)],
                'journal_id': deferred_journal.id,
                'company_id': self.company_id.id,
                'partner_id': line.partner_id.id,
                'date': line.move_id.invoice_date + relativedelta(day=31),
                'auto_post': 'at_date',
                'ref': ref,
            })
            # We write the lines after creation, to make sure the `deferred_original_move_ids` is set.
            # This way we can avoid adding taxes for deferred moves.
            move_fully_deferred.write({
                'line_ids': [
                    Command.create(
                        self.env['account.move.line']._get_deferred_lines_values(account.id, coeff * line.balance, ref, line.analytic_distribution, line)
                    ) for (account, coeff) in [(line.account_id, -1), (deferred_account, 1)]
                ],
            })
            line.move_id.deferred_move_ids |= move_fully_deferred
            move_fully_deferred._post(soft=True)

            # Create the deferred entries for the periods [deferred_start_date, deferred_end_date]
            remaining_balance = line.balance
            for period_index, period in enumerate(periods):
                deferral_move = self.create({
                    'move_type': 'entry',
                    'deferred_original_move_ids': [Command.set(line.move_id.ids)],
                    'journal_id': deferred_journal.id,
                    'partner_id': line.partner_id.id,
                    'date': period[1],
                    'auto_post': 'at_date',
                    'ref': ref,
                })
                # For the last deferral move the balance is forced to remaining balance to avoid rounding errors
                force_balance = remaining_balance if period_index == len(periods) - 1 else None
                # Same as before, to avoid adding taxes for deferred moves.
                deferral_move.write({
                    'line_ids': self._get_deferred_lines(line, deferred_account, period, ref, force_balance=force_balance),
                })
                remaining_balance -= deferral_move.line_ids[0].balance
                line.move_id.deferred_move_ids |= deferral_move
                deferral_move._post(soft=True)

    def open_deferred_entries(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Deferred Entries"),
            'res_model': 'account.move.line',
            'domain': [('id', 'in', self.deferred_move_ids.line_ids.ids)],
            'views': [(False, 'tree'), (False, 'form')],
            'context': {
                'search_default_group_by_move': True,
                'expand': True,
            }
        }

    def open_deferred_original_entry(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _("Original Deferred Entries"),
            'res_model': 'account.move.line',
            'domain': [('id', 'in', self.deferred_original_move_ids.line_ids.ids)],
            'views': [(False, 'tree'), (False, 'form')],
            'context': {
                'search_default_group_by_move': True,
                'expand': True,
            }
        }
        if len(self.deferred_original_move_ids) == 1:
            action.update({
                'res_model': 'account.move',
                'res_id': self.deferred_original_move_ids[0].id,
                'views': [(False, 'form')],
            })
        return action
