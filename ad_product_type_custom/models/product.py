from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'product.template'

    service_tracking = fields.Selection(
        selection=[
            ('no', 'Nothing'),
            ('task_global_project', 'Task'),
            ('task_in_project', 'Project & Task'),
            ('project_only', 'Project'),
        ],
        string="Create on Order", default="no",
        help="On Sales order confirmation, this product can generate a project and/or task. \
            From those, you can track the service you are selling.\n \
            'In sale order\'s project': Will use the sale order\'s configured project if defined or fallback to \
            creating a new project based on the selected template.")







