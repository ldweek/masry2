# -*- coding: utf-8 -*-

##############################################################################
#
#
#    Copyright (C) 2020-TODAY .
#    Author: Eng.Ramadan Khalil (<rkhalil1990@gmail.com>)
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
##############################################################################

import pytz
from datetime import datetime, date, timedelta, time
from dateutil.relativedelta import relativedelta
from odoo import models, fields, tools, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date
# from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY, \
#     make_aware, datetime_to_string, string_to_datetime

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


class AttendanceSheet(models.Model):
    _name = 'attendance.sheet'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Hr Attendance Sheet'

    name = fields.Char("name")
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',
                                  required=True)

    batch_id = fields.Many2one(comodel_name='attendance.sheet.batch',
                               string='Attendance Sheet Batch')
    department_id = fields.Many2one(related='employee_id.department_id',
                                    string='Department', store=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 copy=False, required=True,
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]})
    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=lambda self: fields.Date.to_string(
                                date.today().replace(day=1)), )
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1,
                                                              days=-1)).date()))
    line_ids = fields.One2many(comodel_name='attendance.sheet.line',
                               string='Attendances', readonly=True,
                               inverse_name='att_sheet_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], default='draft', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True,
        help=' * The \'Draft\' status is used when a HR user is creating a new  attendance sheet. '
             '\n* The \'Confirmed\' status is used when  attendance sheet is confirmed by HR user.'
             '\n* The \'Approved\' status is used when  attendance sheet is accepted by the HR Manager.')
    no_overtime = fields.Integer(compute="_compute_sheet_total",
                                 string="No of overtimes", readonly=True,
                                 store=True)
    tot_overtime = fields.Float(compute="_compute_sheet_total",
                                string="Total Over Time", readonly=True,
                                store=True)
    tot_difftime = fields.Float(compute="_compute_sheet_total",
                                string="Total Diff time Hours", readonly=True,
                                store=True)
    no_difftime = fields.Integer(compute="_compute_sheet_total",
                                 string="No of Diff Times", readonly=True,
                                 store=True)
    tot_late = fields.Float(compute="_compute_sheet_total",
                            string="Total Late In", readonly=True, store=True)
    no_late = fields.Integer(compute="_compute_sheet_total",
                             string="No of Lates",
                             readonly=True, store=True)
    no_absence = fields.Integer(compute="_compute_sheet_total",
                                string="No of Absence Days", readonly=True,
                                store=True)
    no_leave = fields.Integer(compute="_compute_sheet_total",
                                string="No of Absence Days", readonly=True,
                                store=True)
    no_leave_sick = fields.Integer(compute="_compute_sheet_total",
                                string="No of Absence Days", readonly=True,
                                store=True)
    no_leave_deduct = fields.Integer(compute="_compute_sheet_total",
                                string="No of Absence Days", readonly=True,
                                store=True)
    no_leave_pregnancy = fields.Integer(compute="_compute_sheet_total",
                                string="No of Absence Days", readonly=True,
                                store=True)
    no_leave_work_injury = fields.Integer(compute="_compute_sheet_total",
                                string="No of Absence Days", readonly=True,
                                store=True)
    no_leave_work_permission = fields.Integer(compute="_compute_sheet_total",
                                string="No of Absence Days", readonly=True,
                                store=True)
    tot_absence = fields.Float(compute="_compute_sheet_total",
                               string="Total absence Hours", readonly=True,
                               store=True)
    tot_worked_hour = fields.Float(compute="_compute_sheet_total",
                                   string="Total Late In", readonly=True,
                                   store=True)
    att_policy_id = fields.Many2one(comodel_name='hr.attendance.policy',
                                    string="Attendance Policy ", required=True)
    payslip_id = fields.Many2one(comodel_name='hr.payslip', string='PaySlip')

    contract_id = fields.Many2one('hr.contract', string='Contract',
                                  readonly=True,
                                  states={'draft': [('readonly', False)]})
    total_worked_hours = fields.Float(string="", required=False, compute="get_total_worked_hours")
    @api.depends('employee_id', 'date_from', 'date_to')
    def get_total_worked_hours(self):
        # employee = self.employee_id
        # date_from = self.date_from
        # date_to = self.date_to
        total = 0.0
        for rec in self:
            employee = rec.employee_id
            date_from = rec.date_from
            date_to = rec.date_to
            if rec.employee_id and rec.date_from and rec.date_to:
                all_worked_days = self.env['hr.attendance'].search(
                    [('employee_id', '=', employee.id), ('check_in', '>=', date_from), ('check_out', '<=', date_to), ])
                print(all_worked_days)
                if all_worked_days:
                    print(all_worked_days)
                    for work_day in all_worked_days:
                        total += work_day.worked_hours
                    rec.total_worked_hours = total
                else:
                    rec.total_worked_hours = 0.0
            else:
                rec.total_worked_hours = 0.0

    # TODO allowances fields
    house_allowances = fields.Float(string="منحة غلاء معيشه")
    overtime_allowance = fields.Float(string="علاوة اضافيه")
    treatment_allowance = fields.Float(string="علاوة سنوات سابقه")
    transport_allowances = fields.Float(string="بدل انتقال")
    living_allowances = fields.Float(string="علاوة يوليو")
    nature_of_work_allowances = fields.Float(string="غلاء معيشة")
    telephone_allowance = fields.Float(string="بدل تليفون")
    bonus_request = fields.Float()
    bonus_request_sale = fields.Float('تسوية')
    overtime_request = fields.Float()

    # TODO NEW Allowances fields
    Regular_bonus_for_managers = fields.Float(string="مكافئة انتظام للمديرين",  required=False, )
    Regular_regularity_equivalent = fields.Float(string="مكافئة انتظام عادية",  required=False, )
    Incentive_bonus = fields.Float(string="مكافئات تشجيعيه",  required=False, )
    motivation = fields.Float(string="الحافز",  required=False, )
    profit_account = fields.Float(string="حساب ارباح",  required=False, )

    # TODO deductions fields
    general_deductions = fields.Float()
    social_insurance_deductions = fields.Float(string="سلفة تأمينات")
    medical_insurance_deductions = fields.Float(string="سلفة ايصال نقدية")
    fingerprint_deductions = fields.Float(string="صندوق طوارئ")
    administrative_deductions = fields.Float(string="صندوق زماله")
    absence_without_permission_deductions = fields.Float(string="تأمين اجتماعي")
    profit_tax_percent = fields.Float(string="اشتراك جمعية")

    penalty = fields.Float('Total Penalty')
    penalty_sale = fields.Float('تسوية دائنة')

    loans = fields.Float(string="Loans",  required=False, )

    def update_all_allowance_and_deduction_fields(self):
        employee = self.employee_id
        domain = [('employee_id', '=', employee.id), ('state', '=', 'open'), ]
        contract_object = self.env['hr.contract'].search(domain)
        print("contract_object >>>>>>>>>>>>>>", contract_object)
        self.house_allowances = 0.0
        self.overtime_allowance = 0.0
        self.treatment_allowance = 0.0
        self.transport_allowances = 0.0
        self.living_allowances = 0.0
        self.nature_of_work_allowances = 0.0
        self.telephone_allowance = 0.0
        self.profit_tax_percent = 0.0
        self.Regular_bonus_for_managers = 0.0
        self.Regular_regularity_equivalent = 0.0
        self.motivation = 0.0
        self.profit_account = 0.0

    def update_current_penalty_to_paid(self):
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        total_amount = 0
        total_amount_s = 0

        domain = [('employee_id', '=', employee.id), ('state', '=', 'confirm')]
        penalty_for_emp = self.env['penalty.request'].search(domain + [('det_type','=','default')])
        penalty_for_emp_sale = self.env['penalty.request'].search(domain + [('det_type','=','sale')])

        print("penalty_objects >", penalty_for_emp)
        for loan in penalty_for_emp:
            penalty_ids = loan.penalty_ids.filtered(lambda x: not x.paid and x.date >= date_from and x.date <= date_to)
            print('penalty_ids', penalty_ids)
            for pay in penalty_ids:
                total_amount += pay.amount
                pay.write({'paid': True})
        for loan in penalty_for_emp_sale:
            penalty_ids = loan.penalty_ids.filtered(lambda x: not x.paid and x.date >= date_from and x.date <= date_to)
            print('penalty_ids', penalty_ids)
            for pay in penalty_ids:
                total_amount_s += pay.amount
                pay.write({'paid': True})
        self.penalty = total_amount
        self.penalty_sale = total_amount_s

    def update_current_total_bonus_request_allowance(self):
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        total_amount = 0
        total_amount_over = 0
        total_amount_sale = 0

        bonus_objects = self.env['bonus.request'].search([('employee_id', '=', employee.id), ('request_date', '>=', date_from), ('request_date', '<=', date_to), ('state', '=', 'confirm'),('is_overtime','=',False),('det_type','=','default')])
        bonus_objects_sale = self.env['bonus.request'].search([('employee_id', '=', employee.id), ('request_date', '>=', date_from), ('request_date', '<=', date_to), ('state', '=', 'confirm'),('det_type','=','sale')])

        overtime_objects = self.env['bonus.request'].search([('employee_id', '=', employee.id), ('request_date', '>=', date_from), ('request_date', '<=', date_to), ('state', '=', 'confirm'),('is_overtime','=',True),('det_type','=','default')])
        print("bonus_objects >", bonus_objects)
        if bonus_objects:
            for bonus in bonus_objects:
                if bonus.bonus_amount > 0:
                    total_amount += bonus.bonus_amount
        for bonus in bonus_objects_sale:
            if bonus.bonus_amount > 0:
                total_amount_sale += bonus.bonus_amount
        if overtime_objects:
            for bonus in overtime_objects:
                if bonus.bonus_amount > 0:
                    total_amount_over += bonus.bonus_amount
        
        print("total_bonus", total_amount)
        print("===================================")
        self.bonus_request = total_amount
        self.overtime_request = total_amount_over
        self.bonus_request_sale = total_amount_sale
        

    def update_current_loan_to_paid(self):
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        total_amount = 0
        domain = [('employee_id', '=', employee.id), ('state', '=', 'approve')]
        loans_for_emp = self.env['hr.loan'].search(domain)
        print("loans_objects >", loans_for_emp)
        for loan in loans_for_emp:
            payment_ids = loan.loan_lines.filtered(
                lambda x: not x.paid and x.date >= date_from and x.date <= date_to)
            for pay in payment_ids:
                total_amount += pay.amount
                pay.write({'paid': True})
        print('total_loan', total_amount)
        print("===================================")
        self.loans = total_amount


    # def unlink(self):
    #     if any(self.filtered(
    #             lambda att: att.state not in ('draft', 'confirm'))):
    #         # TODO:un comment validation in case on non testing
    #         pass
    #         # raise UserError(_(
    #         #     'You cannot delete an attendance sheet which is '
    #         #     'not draft or confirmed!'))
    #     return super(AttendanceSheet, self).unlink()

    def unlink(self):
        print('call from ulink')
        for line in self:
            print('*******************************************************************')
            if line.state == 'draft':
                print('draft')
                res = super(AttendanceSheet, self).unlink()
                return res
            elif line.state == 'confirm':
                print('cofirm')
                raise UserError(_("You can't delete attendance sheets after confirm."))
            elif line.state == 'done':
                raise UserError(_("You can't delete attendance sheets after approve."))

    @api.constrains('date_from', 'date_to')
    def check_date(self):
        for sheet in self:
            emp_sheets = self.env['attendance.sheet'].search(
                [('employee_id', '=', sheet.employee_id.id),
                 ('id', '!=', sheet.id)])
            for emp_sheet in emp_sheets:
                if max(sheet.date_from, emp_sheet.date_from) < min(
                        sheet.date_to, emp_sheet.date_to):
                    raise UserError(_(
                        'You Have Already Attendance Sheet For That '
                        'Period  Please pick another date !'))

    def action_confirm(self):
        self.update_all_allowance_and_deduction_fields()
        self.update_current_penalty_to_paid()
        self.update_current_loan_to_paid()
        self.update_current_total_bonus_request_allowance()

        self.write({'state': 'confirm'})

    def action_approve(self):
        self.action_create_payslip()
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return
        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        self.name = 'Attendance Sheet - %s - %s' % (self.employee_id.name or '',
                                                    format_date(self.env,
                                                                self.date_from,
                                                                date_format="MMMM y"))
        self.company_id = employee.company_id
        contracts = employee._get_contracts(date_from, date_to)
        if not contracts:
            contracts = self.env['hr.contract'].search([('state','=','cancel'),('resg_date','>=',date_to)])
        if not contracts:
            raise ValidationError(
                _('There Is No Valid Contract For Employee %s' % employee.name))
        self.contract_id = contracts[0]
        if not self.contract_id.att_policy_id:
            raise ValidationError(_(
                "Employee %s does not have attendance policy" % employee.name))
        self.att_policy_id = self.contract_id.att_policy_id

    @api.depends('line_ids.overtime', 'line_ids.diff_time', 'line_ids.late_in')
    def _compute_sheet_total(self):
        """
        Compute Total overtime,late ,absence,diff time and worked hours
        :return:
        """
        for sheet in self:
            # Compute Total Overtime
            leave_lines = sheet.line_ids.filtered(lambda l:  l.status == "leave")
            sheet.no_leave = len(leave_lines)
            leave_lines_sick = sheet.line_ids.filtered(lambda l:  l.status == "sick")
            sheet.no_leave_sick = len(leave_lines_sick)
            leave_lines_deduct = sheet.line_ids.filtered(lambda l:  l.status == "deduct_leave")
            sheet.no_leave_deduct = len(leave_lines_deduct)
            leave_lines_preg = sheet.line_ids.filtered(lambda l:  l.status == "pregnancy")
            sheet.no_leave_pregnancy = len(leave_lines_preg)
            leave_lines_inj = sheet.line_ids.filtered(lambda l:  l.status == "work_injury")
            sheet.no_leave_work_injury = len(leave_lines_inj)
            leave_lines_perm = sheet.line_ids.filtered(lambda l:  l.status == "permission")
            sheet.no_leave_work_permission = len(leave_lines_perm)
            overtime_lines = sheet.line_ids.filtered(lambda l: l.overtime > 0)
            sheet.tot_overtime = sum([l.overtime for l in overtime_lines])
            sheet.no_overtime = len(overtime_lines)
            # Compute Total Late In
            late_lines = sheet.line_ids.filtered(lambda l: l.late_in > 0)
            sheet.tot_late = sum([l.late_in for l in late_lines])
            sheet.no_late = len(late_lines)

            # Compute Absence
            absence_lines = sheet.line_ids.filtered(
                lambda l: l.diff_time > 0 and l.status == "ab")
            print('absence_lines=====>',absence_lines)
            sheet.tot_absence = sum([l.diff_time for l in absence_lines])
            sheet.no_absence = len(absence_lines)


            # conmpute earlyout
            diff_lines = sheet.line_ids.filtered(lambda l: l.diff_time > 0 and l.status != "ab")
            print('absence_lines=====>',absence_lines)
            sheet.tot_difftime = sum([l.diff_time for l in diff_lines])
            sheet.no_difftime = len(diff_lines)

    def _get_float_from_time(self, time):
        str_time = datetime.strftime(time, "%H:%M")
        split_time = [int(n) for n in str_time.split(":")]
        float_time = split_time[0] + split_time[1] / 60.0
        return float_time

    def get_attendance_intervals(self, employee, day_start, day_end, tz):
        """

        :param employee:
        :param day_start:datetime the start of the day in datetime format
        :param day_end: datetime the end of the day in datetime format
        :return:
        """
        day_start_native = day_start.replace(tzinfo=tz).astimezone(
            pytz.utc).replace(tzinfo=None)
        day_end_native = day_end.replace(tzinfo=tz).astimezone(
            pytz.utc).replace(tzinfo=None)
        res = []
        attendances = self.env['hr.attendance'].sudo().search(
            [('employee_id', '=', employee.id),
             ('check_in', '>=', day_start_native),
             ('check_in', '<=', day_end_native)],
            order="check_in")
        for att in attendances:
            check_in = att.check_in
            check_out = att.check_out
            if not check_out:
                continue
            res.append((check_in, check_out))
        return res

    def _get_emp_leave_intervals(self, emp, start_datetime=None,
                                 end_datetime=None):
        leaves = []
        leave_obj = self.env['hr.leave']
        leave_ids = leave_obj.search([
            ('employee_id', '=', emp.id),
            ('state', '=', 'validate')])
        for leave in leave_ids:
            date_from = leave.date_from
            if end_datetime and date_from > end_datetime:
                continue
            date_to = leave.date_to
            if start_datetime and date_to < start_datetime:
                continue
            status = 'leave'
            if leave.holiday_status_id.is_mission:
                status = 'mission'
            if leave.holiday_status_id.is_sick:
                status = 'sick'
            if leave.holiday_status_id.is_deduct_leave:
                status = 'deduct_leave'
            if leave.holiday_status_id.is_pregnancy:
                status = 'pregnancy'
            if leave.holiday_status_id.is_work_injury:
                status = 'work_injury'
            if leave.holiday_status_id.is_permission:
                status = 'permission'
                
            leaves.append((date_from, date_to,leave.holiday_status_id.is_deduct,status))
        return leaves

    def get_public_holiday(self, date, emp):
        public_holiday = []
        public_holidays = self.env['hr.public.holiday'].sudo().search(
            [('date_from', '<=', date), ('date_to', '>=', date),
             ('state', '=', 'active')])
        print('publick_hoildays=====>', public_holidays)
        for ph in public_holidays:
            print('ph is', ph.name, [e.name for e in ph.emp_ids])
            if not ph.emp_ids:
                return public_holidays
            if emp.id in ph.emp_ids.ids:
                public_holiday.append(ph.id)
        return public_holiday

    def get_attendances(self):
        print("get_attendances")
        for att_sheet in self:
            att_sheet.line_ids.unlink()
            att_line = self.env["attendance.sheet.line"]
            from_date = max(att_sheet.date_from,att_sheet.contract_id.date_start)
            to_date = att_sheet.date_to
            if att_sheet.contract_id.resg_date:
                to_date = min(to_date,att_sheet.contract_id.resg_date)
            emp = att_sheet.employee_id
            tz = pytz.timezone(emp.tz)
            if not tz:
                raise exceptions.Warning(
                    "Please add time zone for employee : %s" % emp.name)
            calendar_id = emp.contract_id.resource_calendar_id
            shifts_id = emp.contract_id.shifts_line_id

            if not calendar_id:
                raise ValidationError(_(
                    'Please add working hours to the %s `s contract ' % emp.name))
            policy_id = att_sheet.att_policy_id
            print('policy_id here get the policy ',policy_id)
            if not policy_id:
                raise ValidationError(_(
                    'Please add Attendance Policy to the %s `s contract ' % emp.name))

            all_dates = [(from_date + timedelta(days=x)) for x in
                         range((to_date - from_date).days + 1)]
            abs_cnt = 0
            # ********** edit here
            late_cnt = []
            diff_cnt = []
            policy_diff = 0
            for day in all_dates:
                day_start = datetime(day.year, day.month, day.day)
                day_end = day_start.replace(hour=23, minute=59,
                                            second=59)
                day_str = str(day.weekday())
                date = day.strftime('%Y-%m-%d')
                if shifts_id:
                    work_intervals = att_sheet._get_work_intervals(shifts_id, day_start, day_end, tz)

                else:
                    work_intervals = att_sheet._get_work_intervals(calendar_id, day_start, day_end, tz)
                if not work_intervals:
                    work_intervals = att_sheet._get_work_intervals(calendar_id, day_start, day_end, tz)
                work_intervals = calendar_id.att_interval_clean(
                    work_intervals)
                attendance_intervals = self.get_attendance_intervals(emp,
                                                                     day_start,
                                                                     day_end,
                                                                     tz)
                leaves = self._get_emp_leave_intervals(emp, day_start, day_end)
                public_holiday = self.get_public_holiday(date, emp)
                print('publick holiday', public_holiday)
                reserved_intervals = []
                overtime_policy = policy_id.get_overtime()
                abs_flag = False
                if work_intervals:
                    print('work _intervals00',work_intervals)
                    if public_holiday:
                        if attendance_intervals:
                            print('attendance_intervals', attendance_intervals)
                            for attendance_interval in attendance_intervals:
                                overtime = attendance_interval[1] - \
                                           attendance_interval[0]
                                print('over_time after holiday', overtime)
                                float_overtime = overtime.total_seconds() / 3600
                                if float_overtime <= overtime_policy['ph_after']:
                                    act_float_overtime = float_overtime = 0
                                else:
                                    act_float_overtime = (float_overtime-overtime_policy['ph_after'])
                                    float_overtime = (float_overtime -overtime_policy['ph_after']) * \
                                                     overtime_policy['ph_rate']
                                ac_sign_in = pytz.utc.localize(
                                    attendance_interval[0]).astimezone(tz)
                                float_ac_sign_in = self._get_float_from_time(
                                    ac_sign_in)
                                ac_sign_out = pytz.utc.localize(
                                    attendance_interval[1]).astimezone(tz)
                                worked_hours = attendance_interval[1] - \
                                               attendance_interval[0]
                                float_worked_hours = worked_hours.total_seconds() / 3600
                                float_ac_sign_out = float_ac_sign_in + float_worked_hours
                                values = {
                                    'date': date,
                                    'day': day_str,
                                    'ac_sign_in': float_ac_sign_in,
                                    'ac_sign_out': float_ac_sign_out,
                                    'worked_hours': float_worked_hours,
                                    'overtime': float_overtime,
                                    'act_overtime': act_float_overtime,
                                    'att_sheet_id': self.id,
                                    'status': 'ph',
                                    'note': _("working on Public Holiday")
                                }
                                att_line.create(values)
                        else:
                            values = {
                                'date': date,
                                'day': day_str,
                                'att_sheet_id': self.id,
                                'status': 'ph',
                            }
                            att_line.create(values)
                    else:
                        for i, work_interval in enumerate(work_intervals):
                            float_worked_hours = 0
                            att_work_intervals = []
                            diff_intervals = []
                            late_in_interval = []
                            diff_time = timedelta(hours=00, minutes=00,
                                                  seconds=00)
                            late_in = timedelta(hours=00, minutes=00,
                                                seconds=00)
                            overtime = timedelta(hours=00, minutes=00,
                                                 seconds=00)
                            for j, att_interval in enumerate(attendance_intervals):
                                if max(work_interval[0], att_interval[0]) < min(work_interval[1], att_interval[1]):
                                    current_att_interval = att_interval
                                    if i + 1 < len(work_intervals):
                                        next_work_interval = work_intervals[i + 1]
                                        if max(next_work_interval[0],current_att_interval[0]) < min(next_work_interval[1],current_att_interval[1]):
                                            split_att_interval = (next_work_interval[0],current_att_interval[1])
                                            current_att_interval = (current_att_interval[0],next_work_interval[0])
                                            attendance_intervals[j] = current_att_interval
                                            attendance_intervals.insert(j + 1, split_att_interval)
                                    att_work_intervals.append(current_att_interval)
                            reserved_intervals += att_work_intervals
                            pl_sign_in = self._get_float_from_time(
                                pytz.utc.localize(work_interval[0]).astimezone(tz))
                            pl_sign_out = self._get_float_from_time(pytz.utc.localize(work_interval[1]).astimezone(tz))
                            pl_sign_in_time = pytz.utc.localize(
                                work_interval[0]).astimezone(tz)
                            pl_sign_out_time = pytz.utc.localize(
                                work_interval[1]).astimezone(tz)
                            ac_sign_in = 0
                            ac_sign_out = 0
                            status = ""
                            note = ""
                            if att_work_intervals:
                                print('att work intervals',att_work_intervals)
                                if len(att_work_intervals) > 1:
                                    # print("there is more than one interval for that work interval")
                                    late_in_interval = (work_interval[0],att_work_intervals[0][0])
                                    # diff_time_interval = (work_interval[0],att_work_intervals[0][0])
                                    overtime_interval = (work_interval[1],att_work_intervals[-1][1])
                                    if overtime_interval[1] < overtime_interval[0]:
                                        overtime = timedelta(hours=0, minutes=0,seconds=0)
                                    else:
                                        overtime = overtime_interval[1] - \
                                                   overtime_interval[0]
                                    remain_interval = (
                                        att_work_intervals[0][1],
                                        work_interval[1])
                                    # print'first remain intervals is',remain_interval
                                    for att_work_interval in att_work_intervals:
                                        float_worked_hours += (att_work_interval[1] -att_work_interval[0]).total_seconds() / 3600
                                        # print'float worked hors is', float_worked_hours
                                        if att_work_interval[1] <= \
                                                remain_interval[0]:
                                            continue
                                        if att_work_interval[0] >= \
                                                remain_interval[1]:
                                            break
                                        if remain_interval[0] < \
                                                att_work_interval[0] < \
                                                remain_interval[1]:
                                            diff_intervals.append((
                                                remain_interval[
                                                    0],
                                                att_work_interval[
                                                    0]))
                                            remain_interval = (
                                                att_work_interval[1],
                                                remain_interval[1])
                                    if remain_interval and remain_interval[0] <= \
                                            work_interval[1]:
                                        diff_intervals.append((remain_interval[
                                                                   0],
                                                               work_interval[
                                                                   1]))
                                    ac_sign_in = self._get_float_from_time(
                                        pytz.utc.localize(att_work_intervals[0][
                                                              0]).astimezone(
                                            tz))
                                    ac_sign_out = self._get_float_from_time(
                                        pytz.utc.localize(
                                            att_work_intervals[-1][
                                                1]).astimezone(tz))
                                    ac_sign_out = ac_sign_in + ((
                                                                        att_work_intervals[
                                                                            -1][
                                                                            1] -
                                                                        att_work_intervals[
                                                                            0][
                                                                            0]).total_seconds() / 3600)
                                else:
                                    late_in_interval = (work_interval[0],att_work_intervals[0][0])
                                    overtime_interval = (work_interval[1],att_work_intervals[-1][1])
                                    if overtime_interval[1] < overtime_interval[
                                        0]:
                                        overtime = timedelta(hours=0, minutes=0,
                                                             seconds=0)
                                        diff_intervals.append((
                                            overtime_interval[
                                                1],
                                            overtime_interval[
                                                0]))
                                    else:
                                        overtime = overtime_interval[1] - \
                                                   overtime_interval[0]
                                    ac_sign_in = self._get_float_from_time(
                                        pytz.utc.localize(att_work_intervals[0][
                                                              0]).astimezone(
                                            tz))
                                    ac_sign_out = self._get_float_from_time(
                                        pytz.utc.localize(att_work_intervals[0][
                                                              1]).astimezone(
                                            tz))
                                    worked_hours = att_work_intervals[0][1] - \
                                                   att_work_intervals[0][0]
                                    float_worked_hours = worked_hours.total_seconds() / 3600
                                    ac_sign_out = ac_sign_in + float_worked_hours
                            else:
                                late_in_interval = []
                                diff_intervals.append((work_interval[0], work_interval[1]))
                                print('diff_intervals=====>',diff_intervals)
                                status = "ab"
                            if diff_intervals:
                                for diff_in in diff_intervals:
                                    if leaves:
                                        status = "leave" 
                                        for leave in leaves:
                                            status = leave[3]
                                        diff_clean_intervals = calendar_id.att_interval_without_leaves(
                                            diff_in, leaves)
                                        for diff_clean in diff_clean_intervals:
                                            diff_time += diff_clean[1] - \
                                                         diff_clean[0]
                                            print('diff_time ===>',diff_time )
                                    else:
                                        diff_time += diff_in[1] - diff_in[0]
                            if late_in_interval:
                                if late_in_interval[1] < late_in_interval[0]:
                                    late_in = timedelta(hours=0, minutes=0,
                                                        seconds=0)
                                else:
                                    if leaves:
                                        late_clean_intervals = calendar_id.att_interval_without_leaves(
                                            late_in_interval, leaves)
                                        for late_clean in late_clean_intervals:
                                            late_in += late_clean[1] - \
                                                       late_clean[0]

                                    else:
                                        late_in = late_in_interval[1] - \
                                                  late_in_interval[0]
                            float_overtime = overtime.total_seconds() / 3600
                            print('latein========>',late_in)
                            print('********** flot overtime', float_overtime)
                            print('********** over time policy active after', overtime_policy['wd_after'])
                            if float_overtime <= overtime_policy['wd_after']:
                                act_float_overtime = float_overtime = 0
                                print('float over time if 1' , act_float_overtime)

                            else:
                                # ********* edit here apply after
                                act_float_overtime = float_overtime - overtime_policy['wd_after']
                                print('******* else ====> act float over time after active after', act_float_overtime)
                                float_overtime = act_float_overtime * \
                                                 overtime_policy['wd_rate']
                                print('float over time finally ',float_overtime)
                            float_late = late_in.total_seconds() / 3600
                            act_float_late = late_in.total_seconds() / 3600
                            policy_late, late_cnt = policy_id.get_late(float_late,late_cnt)
                            print(' policy_late', policy_late)
                            print(' late_cnt',late_cnt)
                            float_diff = diff_time.total_seconds() / 3600
                            print('float_diff after late',float_diff)
                            if status == 'ab':
                                if not abs_flag:
                                    abs_cnt += 1
                                abs_flag = True
                                act_float_diff = float_diff
                                print('float_dif if ab fun', float_diff)
                                policy_diff = policy_id.get_absence(float_diff,abs_cnt)

                            else:
                                # ************ edit here  float diff
                                act_float_diff = float_diff
                                float_diff = diff_time.total_seconds() / 3600
                                act_float_diff = diff_time.total_seconds() / 3600
                                print('act_float_diff ===>', act_float_diff)
                                policy_diff,diff_cnt= policy_id.get_diff(float_diff,diff_cnt)
                                print('policy_diff ===>',policy_diff)
                                print('diff_cnt ===>',diff_cnt)
                            values = {
                                'date': date,
                                'day': day_str,
                                'pl_sign_in': pl_sign_in,
                                'pl_sign_out': pl_sign_out,
                                'ac_sign_in': ac_sign_in,
                                'ac_sign_out': ac_sign_out,
                                'late_in': policy_late,
                                'act_late_in': act_float_late,
                                'worked_hours': float_worked_hours,
                                'overtime': float_overtime,
                                'act_overtime': act_float_overtime,
                                'diff_time': policy_diff,
                                'act_diff_time': act_float_diff,
                                'status': status,
                                'att_sheet_id': self.id
                            }
                            # values = {
                            #     'date': date,
                            #     'day': day_str,
                            #     'pl_sign_in': pl_sign_in,
                            #     'pl_sign_out': pl_sign_out,
                            #     'ac_sign_in': ac_sign_in,
                            #     'ac_sign_out': ac_sign_out,
                            #     'late_in': policy_late,
                            #     'act_late_in': act_float_late,
                            #     'worked_hours': float_worked_hours,
                            #     'overtime': act_float_overtime,
                            #     'act_overtime': float_overtime,
                            #     'diff_time': policy_diff,
                            #     'act_diff_time': act_float_diff,
                            #     'status': status,
                            #     'att_sheet_id': self.id
                            # }
                            att_line.create(values)
                            print('values',values)
                        out_work_intervals = [x for x in attendance_intervals if
                                              x not in reserved_intervals]
                        if out_work_intervals:
                            for att_out in out_work_intervals:
                                overtime = att_out[1] - att_out[0]
                                ac_sign_in = self._get_float_from_time(
                                    pytz.utc.localize(att_out[0]).astimezone(
                                        tz))
                                ac_sign_out = self._get_float_from_time(
                                    pytz.utc.localize(att_out[1]).astimezone(
                                        tz))
                                float_worked_hours = overtime.total_seconds() / 3600
                                ac_sign_out = ac_sign_in + float_worked_hours
                                float_overtime = overtime.total_seconds() / 3600
                                if float_overtime <= overtime_policy['wd_after']:
                                    float_overtime = act_float_overtime = 0
                                else:
                                    act_float_overtime = float_overtime
                                    float_overtime = act_float_overtime * \
                                                     overtime_policy['wd_rate']
                                values = {
                                    'date': date,
                                    'day': day_str,
                                    'pl_sign_in': 0,
                                    'pl_sign_out': 0,
                                    'ac_sign_in': ac_sign_in,
                                    'ac_sign_out': ac_sign_out,
                                    'overtime': float_overtime,
                                    'worked_hours': float_worked_hours,
                                    'act_overtime': act_float_overtime,
                                    'note': _("overtime out of work intervals"),
                                    'att_sheet_id': self.id
                                }
                                att_line.create(values)
                else:
                    if attendance_intervals:
                        # print "thats weekend be over time "
                        for attendance_interval in attendance_intervals:
                            overtime = attendance_interval[1] - \
                                       attendance_interval[0]
                            ac_sign_in = pytz.utc.localize(
                                attendance_interval[0]).astimezone(tz)
                            ac_sign_out = pytz.utc.localize(
                                attendance_interval[1]).astimezone(tz)
                            float_overtime = overtime.total_seconds() / 3600
                            if float_overtime <= overtime_policy['we_after']:
                                float_overtime = 0
                                act_float_overtime = 0
                            else:
                                # act_float_overtime = float_overtime
                                # float_overtime = act_float_overtime * \
                                #                  overtime_policy['we_rate']
                                #
                                # edit here apply after week end
                                act_float_overtime = float_overtime - overtime_policy['we_after']
                                float_overtime = act_float_overtime * \
                                             overtime_policy['we_rate']
                            ac_sign_in = pytz.utc.localize(
                                attendance_interval[0]).astimezone(tz)
                            ac_sign_out = pytz.utc.localize(
                                attendance_interval[1]).astimezone(tz)
                            worked_hours = attendance_interval[1] - \
                                           attendance_interval[0]
                            float_worked_hours = worked_hours.total_seconds() / 3600
                            values = {
                                'date': date,
                                'day': day_str,
                                'ac_sign_in': self._get_float_from_time(
                                    ac_sign_in),
                                'ac_sign_out': self._get_float_from_time(
                                    ac_sign_out),
                                'overtime': float_overtime,
                                'act_overtime': act_float_overtime,
                                'worked_hours': float_worked_hours,
                                'att_sheet_id': self.id,
                                'status': 'weekend',
                                'note': _("working in weekend")
                            }
                            att_line.create(values)
                    else:
                        values = {
                            'date': date,
                            'day': day_str,
                            'att_sheet_id': self.id,
                            'status': 'weekend',
                            'note': ""
                        }
                        att_line.create(values)

    def _get_work_intervals(self, calendar, day_start, day_end, tz):
        self.ensure_one()
        return calendar.att_get_work_intervals(day_start, day_end, tz)

    def action_payslip(self):
        self.ensure_one()
        payslip_id = self.payslip_id
        if not payslip_id:
            payslip_id = self.action_create_payslip()[0]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': payslip_id.id,
            'views': [(False, 'form')],
        }

    def action_create_payslip(self):
        payslip_obj = self.env['hr.payslip']
        payslips = payslip_obj
        for sheet in self:
            contracts = sheet.employee_id._get_contracts(sheet.date_from,
                                                         sheet.date_to)
            if not contracts:
                raise ValidationError(_('There is no active contract for current employee'))
            if sheet.payslip_id:
                raise ValidationError(_('Payslip Has Been Created Before'))
            new_payslip = payslip_obj.new({
                'employee_id': sheet.employee_id.id,
                'date_from': sheet.date_from,
                'date_to': sheet.date_to,
                'contract_id': contracts[0].id,
                'struct_id': contracts[0].structure_type_id.default_struct_id.id
            })
            new_payslip._compute_contract_id()
            new_payslip._compute_name()
            payslip_dict = new_payslip._convert_to_write({
                name: new_payslip[name] for name in new_payslip._cache})

            payslip_id = payslip_obj.create(payslip_dict)
            worked_day_lines = self._get_workday_lines()
            payslip_id.worked_days_line_ids = [(0, 0, x) for x in
                                               worked_day_lines]
            payslip_id.compute_sheet()
            sheet.payslip_id = payslip_id
            payslips += payslip_id
        return payslips

    def _get_workday_lines(self):
        self.ensure_one()

        work_entry_obj = self.env['hr.work.entry.type']
        overtime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHOT')])
        latin_work_entry = work_entry_obj.search([('code', '=', 'ATTSHLI')])
        absence_work_entry = work_entry_obj.search([('code', '=', 'ATTSHAB')])
        leave_work_entry = work_entry_obj.search([('code', '=', 'ATTSHLV')])
        leave_work_entry_sick = work_entry_obj.search([('code', '=', 'ATTSHS')])
        leave_work_entry_deduct = work_entry_obj.search([('code', '=', 'ATTSHDEDUCT')])
        leave_work_entry_pregnancy = work_entry_obj.search([('code', '=', 'ATTSHPREG')])
        leave_work_entry_injury = work_entry_obj.search([('code', '=', 'ATTSHINJ')])
        leave_work_entry_permission = work_entry_obj.search([('code', '=', 'ATTSHP')])
        loan_work_entry = work_entry_obj.search([('code', '=', 'ATTSILOANSDED')])

        difftime_work_entry = work_entry_obj.search([('code', '=', 'ATTSHDT')])
        penaltya_work_entry = work_entry_obj.search([('code', '=', 'ATTSHTPENDED')])
        penaltya_work_entry_s = work_entry_obj.search([('code', '=', 'ATTSHTPENDEDS')])

        bonus_request_work_entry = work_entry_obj.search([('code', '=', 'ATTSHBR')])
        bonus_request_sale_work_entry = work_entry_obj.search([('code', '=', 'ATTSHBRS')])

        overtime_request_work_entry = work_entry_obj.search([('code', '=', 'ATTSHBRO')])
        loan_deductions = [{
            'name': "Loan",
            'code': 'Loan',
            'work_entry_type_id': loan_work_entry[0].id,
            'sequence': 110,
            'number_of_days': self.loans,
            'number_of_hours': self.loans,
        }]
        penalty_deductions = [{
            'name': "Employee Penalty",
            'code': 'EmployeePenalty',
            'work_entry_type_id': penaltya_work_entry[0].id,
            'sequence': 115,
            'number_of_days': 0,
            'number_of_hours': self.penalty,
        }]
        penalty_deductions_s = [{
            'name': "تسوية دائنة",
            'code': 'EmployeePenaltyS',
            'work_entry_type_id': penaltya_work_entry_s[0].id,
            'sequence': 115,
            'number_of_days': 0,
            'number_of_hours': self.penalty_sale,
        }]
        bonus_request_allowance = [{
            'name': "BONUS REQUEST ALLOWANCE",
            'code': 'BONUSREQUEST',
            'work_entry_type_id': bonus_request_work_entry[0].id,
            'sequence': 135,
            'number_of_days': 0,
            'number_of_hours': self.bonus_request,
        }]
        bonus_sale_request_allowance = [{
            'name': "BONUS REQUEST ALLOWANCE",
            'code': 'BONUSREQUESTS',
            'work_entry_type_id': bonus_request_sale_work_entry[0].id,
            'sequence': 136,
            'number_of_days': 0,
            'number_of_hours': self.bonus_request_sale,
        }]
        overtime_request_allowance = [{
            'name': "Overtime ALLOWANCE",
            'code': 'BONUSREQUESTO',
            'work_entry_type_id': overtime_request_work_entry[0].id,
            'sequence': 136,
            'number_of_days': 0,
            'number_of_hours': self.overtime_request,
        }]

        overtime = [{
            'name': "Overtime",
            'code': 'OVT',
            'work_entry_type_id': overtime_work_entry[0].id,
            'sequence': 30,
            'number_of_days': self.no_overtime,
            'number_of_hours': self.tot_overtime,
        }]
        print('overtimme *********22222',overtime)
        absence = [{
            'name': "Absence",
            'code': 'ABS',
            'work_entry_type_id': absence_work_entry[0].id,
            'sequence': 35,
            'number_of_days': self.no_absence,
            'number_of_hours': self.tot_absence,
        }]
        leave = [{
            'name': "Leave",
            'code': 'LVE',
            'work_entry_type_id': leave_work_entry[0].id,
            'sequence': 35,
            'number_of_days': self.no_leave,
            'number_of_hours': self.no_leave,
        }]
        leave_sick = [{
            'name': "Leave Sick",
            'code': 'LVES',
            'work_entry_type_id': leave_work_entry_sick[0].id,
            'sequence': 36,
            'number_of_days': self.no_leave_sick,
            'number_of_hours': self.no_leave_sick,
        }]
        leave_deduct = [{
            'name': "Leave Deduct",
            'code': 'LVED',
            'work_entry_type_id': leave_work_entry_deduct[0].id,
            'sequence': 37,
            'number_of_days': self.no_leave_deduct,
            'number_of_hours': self.no_leave_deduct,
        }]
        leave_pregnancy = [{
            'name': "Leave Pregnancy",
            'code': 'LVED',
            'work_entry_type_id': leave_work_entry_permission[0].id,
            'sequence': 37,
            'number_of_days': self.no_leave_pregnancy,
            'number_of_hours': self.no_leave_pregnancy,
        }]
        leave_injury = [{
            'name': "Leave Injury",
            'code': 'LVED',
            'work_entry_type_id': leave_work_entry_injury[0].id,
            'sequence': 38,
            'number_of_days': self.no_leave_work_injury,
            'number_of_hours': self.no_leave_work_injury,
        }]
        leave_permission = [{
            'name': "Leave Permission",
            'code': 'LVEPR',
            'work_entry_type_id': leave_work_entry_permission[0].id,
            'sequence': 39,
            'number_of_days': self.no_leave_work_permission,
            'number_of_hours': self.no_leave_work_permission,
        }]
        late = [{
            'name': "Late In",
            'code': 'LATE',
            'work_entry_type_id': latin_work_entry[0].id,
            'sequence': 40,
            'number_of_days': self.no_late,
            'number_of_hours': self.tot_late,
        }]
        difftime = [{
            'name': "Difference time",
            'code': 'DIFFT',
            'work_entry_type_id': difftime_work_entry[0].id,
            'sequence': 45,
            'number_of_days': self.no_difftime,
            'number_of_hours': self.tot_difftime,
        }]
        worked_days_lines = overtime + late + absence + difftime  +  penalty_deductions + bonus_request_allowance + overtime_request_allowance  + leave + loan_deductions + bonus_sale_request_allowance + penalty_deductions_s + leave_permission + leave_sick + leave_deduct + leave_injury + leave_pregnancy
        return worked_days_lines

    def create_payslip(self):
        payslips = self.env['hr.payslip']
        for att_sheet in self:
            if att_sheet.payslip_id:
                continue
            from_date = att_sheet.date_from
            to_date = att_sheet.date_to
            employee = att_sheet.employee_id
            slip_data = self.env['hr.payslip'].onchange_employee_id(from_date,
                                                                    to_date,
                                                                    employee.id,
                                                                    contract_id=False)
            contract_id = slip_data['value'].get('contract_id')
            if not contract_id:
                raise exceptions.Warning(
                    'There is No Contracts for %s That covers the period of the Attendance sheet' % employee.name)
            worked_days_line_ids = slip_data['value'].get(
                'worked_days_line_ids')
            # TODO _____________ AHMED SABER START CUSTOM SALARY ROLES _____________

            house_allowances = [{
                'name': "منحة غلاء معيشه",
                'code': 'HouseAllowance',
                'contract_id': contract_id,
                'sequence': 50,
                'number_of_days': att_sheet.house_allowances,
                'number_of_hours': att_sheet.house_allowances,
            }]
            overtime_allowance = [{
                'name': "علاوة اضافيه",
                'code': 'OVERTIME',
                'contract_id': contract_id,
                'sequence': 55,
                'number_of_days': att_sheet.overtime_allowance,
                'number_of_hours': att_sheet.overtime_allowance,
            }]
            treatment_allowance = [{
                'name': "علاوة سنوات سابقه",
                'code': 'TREAT',
                'contract_id': contract_id,
                'sequence': 60,
                'number_of_days': att_sheet.treatment_allowance,
                'number_of_hours': att_sheet.treatment_allowance,
            }]
            transport_allowances = [{
                'name': "بدل انتقال",
                'code': 'TRANSPORT',
                'contract_id': contract_id,
                'sequence': 65,
                'number_of_days': att_sheet.transport_allowances,
                'number_of_hours': att_sheet.transport_allowances,
            }]
            living_allowances = [{
                'name': "علاوة يوليو",
                'code': 'LIVING',
                'contract_id': contract_id,
                'sequence': 70,
                'number_of_days': att_sheet.living_allowances,
                'number_of_hours': att_sheet.living_allowances,
            }]
            nature_of_work_allowances = [{
                'name': "غلاء معيشة",
                'code': 'NATURE',
                'contract_id': contract_id,
                'sequence': 75,
                'number_of_days': att_sheet.nature_of_work_allowances,
                'number_of_hours': att_sheet.nature_of_work_allowances,
            }]
            telephone_allowance = [{
                'name': "بدل تليفون",
                'code': 'TELEPHONE',
                'contract_id': contract_id,
                'sequence': 80,
                'number_of_days': att_sheet.telephone_allowance,
                'number_of_hours': att_sheet.telephone_allowance,
            }]
            general_deductions = [{
                'name': "General Deductions",
                'code': 'GeneralDeductions',
                'contract_id': contract_id,
                'sequence': 85,
                'number_of_days': att_sheet.general_deductions,
                'number_of_hours': att_sheet.general_deductions,
            }]
            social_insurance_deductions = [{
                'name': "سلفة تأمينات ",
                'code': 'SOCIALINSURANCE',
                'contract_id': contract_id,
                'sequence': 90,
                'number_of_days': att_sheet.social_insurance_deductions,
                'number_of_hours': att_sheet.social_insurance_deductions,
            }]
            medical_insurance_deductions = [{
                'name': "سلفة ايصال نقدية",
                'code': 'MEDICAL',
                'contract_id': contract_id,
                'sequence': 95,
                'number_of_days': att_sheet.medical_insurance_deductions,
                'number_of_hours': att_sheet.medical_insurance_deductions,
            }]
            fingerprint_deductions = [{
                'name': "صندوق طوارئ",
                'code': 'FINGER',
                'contract_id': contract_id,
                'sequence': 100,
                'number_of_days': att_sheet.fingerprint_deductions,
                'number_of_hours': att_sheet.fingerprint_deductions,
            }]
            administrative_deductions = [{
                'name': "صندوق زماله",
                'code': 'ADMIN',
                'contract_id': contract_id,
                'sequence': 105,
                'number_of_days': att_sheet.administrative_deductions,
                'number_of_hours': att_sheet.administrative_deductions,
            }]
            absence_without_permission_deductions = [{
                'name': "تأمين اجتماعي",
                'code': 'ABSENCE',
                'contract_id': contract_id,
                'sequence': 110,
                'number_of_days': att_sheet.absence_without_permission_deductions,
                'number_of_hours': att_sheet.absence_without_permission_deductions,
            }]
            penalty_deductions = [{
                'name': "Employee Penalty",
                'code': 'EmployeePenalty',
                'contract_id': contract_id,
                'sequence': 115,
                'number_of_days': att_sheet.penalty,
                'number_of_hours': att_sheet.penalty,
            }]
            total_worked_hours = [{
                'name': "Worked Hours",
                'code': 'WorkedHours',
                'contract_id': contract_id,
                'sequence': 120,
                'number_of_days': att_sheet.total_worked_hours,
                'number_of_hours': att_sheet.total_worked_hours,
            }]
            loans_deduction = [{
                'name': "LOANS Deduction",
                'code': 'LOANS',
                'contract_id': contract_id,
                'sequence': 125,
                'number_of_days': 0,
                'number_of_hours': att_sheet.loans,
            }]
            profit_tax_percent_deduction = [{
                'name': "اشتراك جمعية",
                'code': 'profittaxpercent',
                'contract_id': contract_id,
                'sequence': 130,
                'number_of_days': 0,
                'number_of_hours': att_sheet.profit_tax_percent,
            }]
            bonus_request_allowance = [{
                'name': "BONUS REQUEST ALLOWANCE",
                'code': 'BONUSREQUEST',
                'contract_id': contract_id,
                'sequence': 135,
                'number_of_days': att_sheet.bonus_request,
                'number_of_hours': att_sheet.bonus_request,
            }]
            bonus_request_allowance = [{
                'name': "Overtime ALLOWANCE",
                'code': 'BONUSREQUESTO',
                'contract_id': contract_id,
                'sequence': 136,
                'number_of_days': att_sheet.overtime_request,
                'number_of_hours': att_sheet.overtime_request,
            }]

            Regular_bonus_for_managers_allowance = [{
                'name': "مكافئة انتظام للمديرين",
                'code': 'Regularbonusformanagers',
                'contract_id': contract_id,
                'sequence': 140,
                'number_of_days': att_sheet.Regular_bonus_for_managers,
                'number_of_hours': att_sheet.Regular_bonus_for_managers,
            }]
            Regular_regularity_equivalent_allowance = [{
                'name': "مكافئة انتظام عادية",
                'code': 'Regularbonusformanagers',
                'contract_id': contract_id,
                'sequence': 145,
                'number_of_days': att_sheet.Regular_regularity_equivalent,
                'number_of_hours': att_sheet.Regular_regularity_equivalent,
            }]
            Incentive_bonus_allowance = [{
                'name': "مكافئات تشجيعيه",
                'code': 'Incentivebonus',
                'contract_id': contract_id,
                'sequence': 150,
                'number_of_days': att_sheet.Incentive_bonus,
                'number_of_hours': att_sheet.Incentive_bonus,
            }]
            motivation_allowance = [{
                'name': "الحافز",
                'code': 'motivationAA',
                'contract_id': contract_id,
                'sequence': 155,
                'number_of_days': att_sheet.motivation,
                'number_of_hours': att_sheet.motivation,
            }]
            profit_account_allowance = [{
                'name': "حساب ارباح",
                'code': 'profitaccount',
                'contract_id': contract_id,
                'sequence': 160,
                'number_of_days': att_sheet.profit_account,
                'number_of_hours': att_sheet.profit_account,
            }]
            # TODO _____________ AHMED SABER END CUSTOM SALARY ROLES _____________
            overtime = [{
                'name': "Overtime",
                'code': 'OVT',
                'contract_id': contract_id,
                'sequence': 30,
                'number_of_days': att_sheet.no_overtime,
                'number_of_hours': att_sheet.tot_overtime,
            }]
            absence = [{
                'name': "Absence",
                'code': 'ABS',
                'contract_id': contract_id,
                'sequence': 35,
                'number_of_days': att_sheet.no_absence,
                'number_of_hours': att_sheet.tot_absence,
            }]
            late = [{
                'name': "Late In",
                'code': 'LATE',
                'contract_id': contract_id,
                'sequence': 40,
                'number_of_days': att_sheet.no_late,
                'number_of_hours': att_sheet.tot_late,
            }]
            difftime = [{
                'name': "Difference time",
                'code': 'DIFFT',
                'contract_id': contract_id,
                'sequence': 45,
                'number_of_days': att_sheet.no_difftime,
                'number_of_hours': att_sheet.tot_difftime,
            }]
            worked_days_line_ids += overtime + late + absence + difftime + house_allowances + overtime_allowance + treatment_allowance + transport_allowances + living_allowances + nature_of_work_allowances + telephone_allowance + general_deductions + social_insurance_deductions + medical_insurance_deductions + fingerprint_deductions + administrative_deductions + absence_without_permission_deductions + penalty_deductions + total_worked_hours + loans_deduction + profit_tax_percent_deduction + bonus_request_allowance + overtime_request_allowance  + Regular_bonus_for_managers_allowance + Regular_regularity_equivalent_allowance + Incentive_bonus_allowance + motivation_allowance + profit_account_allowance

            res = {
                'employee_id': employee.id,
                'name': slip_data['value'].get('name'),
                'struct_id': slip_data['value'].get('struct_id'),
                'contract_id': contract_id,
                'input_line_ids': [(0, 0, x) for x in
                                   slip_data['value'].get('input_line_ids')],
                'worked_days_line_ids': [(0, 0, x) for x in
                                         worked_days_line_ids],
                'date_from': from_date,
                'date_to': to_date,
            }
            new_payslip = self.env['hr.payslip'].create(res)
            att_sheet.payslip_id = new_payslip
            payslips += new_payslip
        return payslips


class AttendanceSheetLine(models.Model):
    _name = 'attendance.sheet.line'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sum', 'Summary'),
        ('confirm', 'Confirmed'),
        ('done', 'Approved')], related='att_sheet_id.state', store=True, )

    date = fields.Date("Date")
    day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], 'Day of Week', required=True, index=True, )
    att_sheet_id = fields.Many2one(comodel_name='attendance.sheet',
                                   ondelete="cascade",
                                   string='Attendance Sheet', readonly=True)
    employee_id = fields.Many2one(related='att_sheet_id.employee_id',
                                  string='Employee')
    pl_sign_in = fields.Float("Planned sign in", readonly=True)
    pl_sign_out = fields.Float("Planned sign out", readonly=True)
    worked_hours = fields.Float("Worked Hours", readonly=True)
    ac_sign_in = fields.Float("Actual sign in", readonly=True)
    ac_sign_out = fields.Float("Actual sign out", readonly=True)
    overtime = fields.Float("Overtime", readonly=True)
    act_overtime = fields.Float("Actual Overtime", readonly=True)
    late_in = fields.Float("Late In", readonly=True)
    diff_time = fields.Float("Diff Time",
                             help="Diffrence between the working time and attendance time(s) ",
                             readonly=True)
    act_late_in = fields.Float("Actual Late In", readonly=True)
    act_diff_time = fields.Float("Actual Diff Time",
                                 help="Diffrence between the working time and attendance time(s) ",
                                 readonly=True)
    status = fields.Selection(string="Status",
                              selection=[('ab', 'Absence'),
                                         ('weekend', 'Week End'),
                                         ('ph', 'Public Holiday'),
                                         ('leave', 'Leave'),
                                        ('mission', 'مأمورية'),
                                        ('sick', 'اجازة مرضي'),
                                        ('deduct_leave', 'اجازة بالخصم'),
                                        ('pregnancy', 'اجتزة وضع'),
                                        ('work_injury', 'خصم اصابة عمل'),
                                        ('permission', 'خصم أذن'),
                                        ],
                              required=False, readonly=True)
    note = fields.Text("Note", readonly=True)
