from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    day_installation = fields.Integer(string="Day", config_parameter='day_installation')
