from odoo import fields, models


class ResCity(models.Model):
    _name = 'res.city'

    name = fields.Char('City Name', required=True)
