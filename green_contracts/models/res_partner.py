from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    full_address = fields.Char(compute='_full_address', size=11)

    def _full_address(self):
        for record in self:
            record.full_address = ', '.join(
                [record.street, record.street2, record.city, record.state_id.name, record.zip, record.country_id.name])

    @api.constrains('phone')
    def len_number_phone(self):
        for rec in self:
            if rec.phone:
                if len(rec.phone) != 11 or not rec.phone.isdigit() or not rec.phone.startswith('01'):
                    raise ValidationError(_('Please entered the phone number and make sure that you entered it correct'))
