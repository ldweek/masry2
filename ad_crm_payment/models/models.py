from odoo import fields, models


class CustomerType(models.Model):
    _name = 'customer.type'

    name = fields.Char(required=True)


class Way(models.Model):
    _name = 'way'

    name = fields.Char(required=True)
