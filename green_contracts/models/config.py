from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tech_commission = fields.Float(config_parameter='tech_commission')
    executive_commission = fields.Float(config_parameter='inspection_commission')
    telesales_commission = fields.Float(config_parameter='telesales_commission')
    out_commission = fields.Float(config_parameter='out_commission')
    executive_manager_commission = fields.Float(config_parameter='inspection_manger_commission')
    tech_manager_commission = fields.Float(config_parameter='tech_manger_commission')

    day_installation = fields.Integer(string="Day", config_parameter='day_installation')

    # floor_ground = fields.Float(config_parameter='floor_ground')
    # floor_1 = fields.Float(config_parameter='floor_1')
    # floor_2 = fields.Float(config_parameter='floor_2')
    # floor_3 = fields.Float(config_parameter='floor_3')
    # floor_4 = fields.Float(config_parameter='floor_4')
    # floor_7 = fields.Float(config_parameter='floor_5_to_7')
    # floor_8 = fields.Float(config_parameter='floor_8')

    first_rate = fields.Float(config_parameter='first_rate_commission',
                              help='Rate commission between amount 700,000 to 1,000,000$')
    second_rate = fields.Float(config_parameter='second_rate_commission',
                               help='Rate commission between amount 1,000,001 to 15,000,000$')
    third_rate = fields.Float(config_parameter='third_rate_commission',
                              help='Rate commission between amount 15,000,001 to 20,000,000$')
    four_rate = fields.Float(config_parameter='four_rate_commission',
                             help='Rate commission between amount 20,000,001 to 25,000,000$')
    five_rate = fields.Float(config_parameter='five_rate_commission',
                             help='Rate commission between amount above 25,000,000$')


    limit_error = fields.Float(config_parameter='limit_error')

    green_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
