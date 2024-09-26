# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class hr_custom_2(models.Model):
    _inherit = 'hr.contract'
    resg_date = fields.Date()
    work_ankle_number = fields.Char('رقم شهادة كعب ')
    work_ankle_date = fields.Date('تاريخ شهادة كعب ')

    def mailmessage(self):
        notification_ids = [(0, 0,
         {
             'res_partner_id': self.hr_responsible_id.partner_id.id,
             'notification_type': 'inbox'
         }
         )]
        vals = {
             'email_from': self.env.user.partner_id.email, # add the sender email
             'author_id': self.env.user.partner_id.id, # add the creator id
             'subtype_id': self.env.ref('mail.mt_comment').id, #Leave this as it is
             'body': 'contract about to expire', # here add the message body
            'record_name' : self.name,
            'notification_ids': notification_ids,
            'model' : 'hr.contract',
            'res_id' : self.id,
            'message_type': 'comment'
          }        
        m = self.env['mail.message'].create(vals)
    def is_contract_ended(self):
        today = fields.Date.today() + timedelta(days=15)
        contracts_ended = self.env['hr.contract'].search([('state','=','open'),('date_end','<=',today)])
        for contract in contracts_ended:
            contract.mailmessage()
    transportation_allowance = fields.Float('بدل انتقال')
    cloth_allowance = fields.Float('بدل ملبس')
    food_allowance = fields.Float('بدل تغذية')
    work_allowance = fields.Float('بدل الدوام')
    work_nature_allowance = fields.Float('بدل طبيعة عمل')
    effort_allowance = fields.Float('بدل جهود')
    other_allowance = fields.Float('بدلات اخرى')
    all = fields.Float('الشامل',compute = '_set_all',readonly = False,store = True)
    @api.depends('transportation_allowance','cloth_allowance','food_allowance','work_nature_allowance','effort_allowance','other_allowance','wage')
    def _set_all(self):
        for rec in self:
            rec.all = rec.transportation_allowance + rec.cloth_allowance + rec.wage + rec.food_allowance + rec.work_nature_allowance + rec.effort_allowance + rec.other_allowance 
    sub_salary = fields.Float('أجر الاشتراك')
    allowance_salary = fields.Float('الراتب التأميني')
    worker_share = fields.Float(compute = '_compute_share',string = 'حصه العامل')
    company_share = fields.Float(compute = '_compute_share',string = 'حصه الشركة')
    intern_date_start = fields.Date('تاريخ بدايه الاختبار')
    intern_date_end = fields.Date(readonly = True,string = 'تاريخ نهاية الاختبار')
    @api.onchange('intern_date_start')
    def _set_intern_date_end(self):
        self.intern_date_end = self.intern_date_start + timedelta(days=90) if self.intern_date_start else False
    @api.depends('allowance_salary')
    def _compute_share(self):
        for rec in self:
            rec.worker_share = 0.11 * rec.allowance_salary
            rec.company_share = (18.75 / 100) * rec.allowance_salary
            
    




class hr_custom(models.Model):
    _name = 'hr.district'
    name = fields.Char()
class hr_custom(models.Model):
    _name = 'hr.center'
    name = fields.Char()
class hr_custom(models.Model):
    _name = 'hr.insurance_state'
    name = fields.Char()
class hr_custom(models.Model):
    _inherit = 'hr.employee'
    _sql_constraints = [ ('unique_code', 'UNIQUE(employee_code)', 'Code must be unique.'),
]
    
    
    id_start_date = fields.Date(string = "ID start date")
    district_id = fields.Many2one('hr.district',string = "القطاع ")
    center_id = fields.Many2one('hr.center',string = "المركز  ")
    state_id = fields.Many2one("res.country.state", string='المحافظة', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    insurance_state_id = fields.Many2one('hr.insurance_state',string = "الموقف التأميني")
    insurance_date = fields.Date(string = "تاريخ التامين")
    medical_number = fields.Char(string = "رقم الشهادة الصحية")
    medical_start_date = fields.Date(string = "تاريخ اصدار الشهادة الصحية")
    medical_end_date = fields.Date(string = "تاريخ انتهاء الشهادة الصحية")
    skill_start_date = fields.Date(string = "تاريخ اصدار قياص المهارة")
    skill_end_date = fields.Date(string = "تاريخ انتهاء قياص المهارة")
    graduation_date = fields.Date(string = "graduation date")
    millitary_end_date = fields.Date(string = "تاريخ انتهاء شهادة التجنيد")
    check_box_1 = fields.Boolean(string = "تاريخ اصدار شهادة التأهيل")
    check_box_2 = fields.Boolean(string = "مسوغات التعيين")
    check_box_3 = fields.Boolean(string = "شهادة الميالد")
    check_box_4 = fields.Boolean(string = "شهادة المؤهل")
    check_box_5 = fields.Boolean(string = "صورة البطاقة")
    check_box_6 = fields.Boolean(string = "نموذج 111")
    check_box_7 = fields.Boolean(string = "كعب العمل")
    check_box_8 = fields.Boolean(string = "شهادة قياس مستوى المهارة")
    check_box_9 = fields.Boolean(string = "شهادة مزاوله مهنة")
    check_box_10 = fields.Boolean(string = "شهادة صحية")
    check_box_11 = fields.Boolean(string = "فيش جنائي")
    check_box_12 = fields.Boolean(string = "صور شخصية")
    check_box_13 = fields.Boolean(string = "طبعة تأمينية")
    check_box_14 = fields.Boolean(string = "كارنيه النقابة")
    check_box_15 = fields.Boolean(string = "صحيفة تدرج اجور")
    check_box_16 = fields.Boolean(string = "صحيفة الجزاءات")
    check_box_17 = fields.Boolean(string = "صحيفة االجازات الرسمية")



    age = fields.Integer(compute = '_set_age')
    @api.depends('birthday')
    def _set_age(self):
        for rec in self:
            if rec.birthday:
                today = fields.Date().today()
                birthdate = rec.birthday
                age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
                rec.age = age
            else:
                rec.age = 0
    my_address = fields.Char('العنوان')
    employee_code = fields.Char('كود الموظف')
    insurance_code = fields.Char('الرقم التاميني')
    isnurance_job = fields.Char('الوظيفة بالتامينات')
    skill_level = fields.Char('قياس مهارة')
    coming_number = fields.Char('رقم الوارد')
    coming_date = fields.Date('تاريخ الوارد')
    medical_check_cret = fields.Boolean('استمارة كشف طبى')
    medical_check = fields.Boolean('كشف طبي')
    recieved_check_id = fields.Boolean('استلام بطاقة الكشف')
    file_number = fields.Char('رقم الملف')
    add_number = fields.Char('رقم القيد')
    license_number = fields.Char('رقم الرخصة')
    license_date_end = fields.Char('تاريخ انتهاء الرخصة')
    millitary_cert_number = fields.Char('رقم شهادة التجنيد')
    military_service_position = fields.Selection(string="", selection=[('not_applicable', 'not applicable'),
                                                                       ('Exempted', 'Exempted'),
                                                                       ('Completed', 'Completed'),
                                                                       ('Postponed', 'Postponed'), ], required=False, )
    bank_number = fields.Char('رقم الحساب البنكى')
    trans_place = fields.Char('مكان الركوب')
    line_1 = fields.Char('خط المواصلات اولى')
    line_2 = fields.Char('خط المواصلات تانية')
    line_3 = fields.Char('خط المواصلات تالتة')

        
