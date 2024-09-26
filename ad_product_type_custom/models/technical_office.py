from odoo import fields, models, api


class TechnicalOffices(models.Model):
    _inherit = 'technical.office'

    task_id = fields.Many2one('project.task' )

