from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY


class AttendanceAbsenceSheetWiz(models.TransientModel):
    _name = "attendance_absence.sheet_wiz"

    date_from = fields.Date(string="From", required=1, default=datetime.today())
    date_to = fields.Date(string="To", required=1, default=datetime.today())
    department_ids = fields.Many2many(comodel_name="hr.department")
    tags_ids = fields.Many2many(comodel_name="hr.employee.category")

    def filter_data(self):
        domain = []
        result = {'name': _('Absence Sheet'), 'res_model': 'attendance_absence.sheet_list', 'view_mode': 'tree',
                  'type': 'ir.actions.act_window', 'domain': False}
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        if self.tags_ids:
            domain.append(('category_ids', 'in', self.tags_ids.ids))
        date_from = datetime(self.date_from.year, self.date_from.month, self.date_from.day, 00, 00, 00)
        date_to = datetime(self.date_to.year, self.date_to.month, self.date_to.day, 00, 00, 00) + relativedelta(days=1)
        employees = self.env['hr.employee'].search(domain)
        attendances = employees.mapped('attendance_ids').filtered(
            lambda m: m.check_in >= date_from and m.check_in < date_to)
        filter_data = []
        for dt in rrule(DAILY, dtstart=date_from, until=date_to - relativedelta(days=1)):
            from_dt = dt
            to_dt = dt + relativedelta(days=1)
            attendances_dt = attendances.filtered(lambda m: m.check_in >= from_dt and m.check_in < to_dt)
            emp_dt = attendances_dt.mapped('employee_id').ids
            employees_dt = employees.filtered(lambda m: m.id not in emp_dt)
            for emp in employees_dt:
                filter_data.append({'employee_id': emp.id, 'absence_date': dt.date()})
        filter_data_ids = self.env['attendance_absence.sheet_list'].create(filter_data)
        result['domain'] = [('id', 'in', filter_data_ids.ids)]
        return result

    class AttendanceAbsenceSheetList(models.TransientModel):
        _name = "attendance_absence.sheet_list"

        employee_id = fields.Many2one(comodel_name="hr.employee", required=1, )
        absence_date = fields.Date(required=1, )
