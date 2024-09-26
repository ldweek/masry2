from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    request_id = fields.Many2one('manufacturing.request')
