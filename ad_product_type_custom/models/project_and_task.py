from odoo import fields, models, api


class Project(models.Model):
    _inherit = 'project.project'

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            ctx = self._context
            if ctx.get('contract_id'):
                vals['contract_id'] = ctx['contract_id']

        return super().create(vals_list)


class Task(models.Model):
    _inherit = 'project.task'
    _rec_name = 'task_relation'

    task_relation = fields.Char(compute='get_name_task_with_relations', store=True)

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} - {rec.project_id.name} - {rec.stage_id.name}"
            result.append((rec.id, name))
        return result

    @api.depends('name', 'project_id', 'stage_id')
    def get_name_task_with_relations(self):
        for task in self:
            name = f"{task.name} - {task.project_id.name} - {task.stage_id.name}"
            task.task_relation = name

    @api.model_create_multi
    def create(self, vals):
        ctx = self._context
        if ctx.get('contract_id'):
            for val in vals:
                val['contract_id'] = ctx['contract_id']
        return super().create(vals)
