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
from operator import itemgetter
from odoo import api, fields, models, _


class ResourceCalendar(models.Model):
    _inherit = "hr.leave.type"
    
    is_deduct = fields.Boolean()
    is_mission = fields.Boolean()
    is_sick = fields.Boolean()
    is_deduct_leave = fields.Boolean()
    is_pregnancy = fields.Boolean()
    is_work_injury = fields.Boolean()
    is_permission = fields.Boolean()
class ResourceCalendar(models.Model):
    _name = "hr.reason"
    name = fields.Char()
class ResourceCalendar(models.Model):
    _inherit = "hr.leave"
    reason = fields.Many2one('hr.reason')
    def refuse_multi(self):
        for rec in self:
            if rec.state in ['confirm','validate1','validate']:
                rec.action_refuse()
    def draft_multi(self):
        for rec in self:
            if rec.state in ['confirm','refuse']:
                rec.action_draft()
    def confirm_multi(self):
        for rec in self:
            if rec.state in ['draft']:
                rec.action_confirm()
    def approve_multi(self):
        for rec in self:
            if rec.state in ['confirm']:
                rec.action_approve()
    def validate_multi(self):
        for rec in self:
            if rec.state in ['validate1']:
                rec.action_validate()