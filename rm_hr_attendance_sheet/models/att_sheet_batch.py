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
# from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import UserError, ValidationError
import babel
from operator import itemgetter
import logging

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


class AttendanceSheetBatch(models.Model):
    _name = 'attendance.sheet.batch'

    name = fields.Char("name")
    department_id = fields.Many2one('hr.department', 'Department Name')
    date_from = fields.Date(string='Date From', readonly=True, required=True,
                            default=lambda self: fields.Date.to_string(
                                date.today().replace(day=1)), )
    date_to = fields.Date(string='Date To', readonly=True, required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1,
                                                              days=-1)).date()))
    att_sheet_ids = fields.One2many(comodel_name='attendance.sheet',
                                    string='Attendance Sheets',
                                    inverse_name='batch_id')
    payslip_batch_id = fields.Many2one(comodel_name='hr.payslip.run',
                                       string='Payslip Batch')
    company_id = fields.Many2one('res.company')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('att_gen', 'Attendance Sheets Generated'),
        ('att_sub', 'Attendance Sheets Submitted'),
        ('done', 'Close')], default='draft', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True, )

    @api.onchange('department_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.department_id) or (not self.date_from) or (
                not self.date_to):
            return
        department = self.department_id
        date_from = self.date_from
        ttyme = datetime.combine(fields.Date.from_string(date_from), time.min)
        locale = self.env.context.get('lang', 'en_US')
        self.name = _('Attendance Batch of %s  Department for %s') % (
            department.name,
            tools.ustr(
                babel.dates.format_date(date=ttyme,
                                        format='MMMM-y',
                                        locale=locale)))

    def action_done(self):
        for batch in self:
            if batch.state != "att_sub":
                continue
            for sheet in batch.att_sheet_ids:
                if sheet.state == 'confirm':
                    sheet.action_approve()
            batch.write({'state': 'done'})

    def action_att_gen(self):
        return self.write({'state': 'att_gen'})

    def gen_att_sheet(self):

        att_sheets = self.env['attendance.sheet']
        att_sheet_obj = self.env['attendance.sheet']
        for batch in self:
            from_date = batch.date_from
            to_date = batch.date_to
            domain = []
            if batch.department_id.id:
                domain.append(('department_id', '=', batch.department_id.id))
            if batch.company_id:
                domain.append(('company_id', '=', batch.company_id.id))
            employee_ids = self.env['hr.employee'].search(domain)

            if not employee_ids:
                raise UserError(_("There is no  Employees In This Department"))
            for employee in employee_ids:

                contract_ids = employee._get_contracts(from_date, to_date)

                if not contract_ids:
                    continue
                new_sheet = att_sheet_obj.new({
                    'employee_id': employee.id,
                    'date_from': from_date,
                    'date_to': to_date,
                    'batch_id': batch.id
                })
                new_sheet.onchange_employee()
                values = att_sheet_obj._convert_to_write(new_sheet._cache)
                att_sheet_id = att_sheet_obj.create(values)

                att_sheet_id.get_attendances()
                att_sheets += att_sheet_id
            batch.action_att_gen()

    def submit_att_sheet(self):
        for batch in self:
            if batch.state != "att_gen":
                continue
            for sheet in batch.att_sheet_ids:
                if sheet.state == 'draft':
                    sheet.action_confirm()

            batch.write({'state': 'att_sub'})

    # *************** edit in batch add button set to draft and delete function
    def action_draft(self):
        for batch in self:
            print('self fron batch ', self)
            print('state batch ', batch.state)
            for sheet in batch.att_sheet_ids:
                print('sheet', sheet.state)
                if sheet.state == 'confirm':
                    sheet.action_draft()
            batch.write({'state': 'att_gen'})

    # def unlink(self):
    #     print('call from ulink from batch ')
    #     print('self from batch ',self)
    #     for batch in self:
    #         print('***************batch',batch)
    #         for sheet in batch.att_sheet_ids:
    #             print('sheet',sheet)
    #             print('atch_att_sheet',batch.att_sheet_ids)
    #             if sheet.state == 'draft':
    #                 print('batch.state',sheet.state)
    #                 sheet_ids = self.env['attendance.sheet'].search([('id','=',sheet.id)])
    #                 print('sheet_ids', sheet_ids)
    #                 sheet_ids.unlink()
    #                 res = super(AttendanceSheetBatch, self).unlink()
    #                 return res
    #             elif sheet.state == 'confirm':
    #                 print('cofirm')
    #                 raise UserError(_("You can't delete attendance sheets after confirm."))
    #             elif sheet.state == 'done':
    #                 raise UserError(_("You can't delete attendance sheets after approve."))



    def unlink(self):
        for batch in self:
            sheet_ids = batch.att_sheet_ids.filtered(lambda s: s.state == 'draft')
            if sheet_ids:
                sheet_ids.unlink()
            for sheet in batch.att_sheet_ids:
                if sheet.state == 'confirm':
                    raise UserError(_("You can't delete attendance sheets after confirm."))
                elif sheet.state == 'done':
                    raise UserError(_("You can't delete attendance sheets after approve."))
        res = super(AttendanceSheetBatch, self).unlink()
        return res