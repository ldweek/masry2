from odoo import models, fields, api


class FleetExpenses(models.Model):
    _name = 'fleet.expenses'

    name = fields.Char()
    description = fields.Text()
