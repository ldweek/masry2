import ast
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.osv.expression import AND


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id.type')
    def _compute_is_service(self):
        for so_line in self:
            so_line.is_service = so_line.product_id.type in ('service', 'product')


    @api.depends('product_id.type')
    def _compute_product_updatable(self):
        super()._compute_product_updatable()
        for line in self:
            if line.product_id.type == 'service' and line.state == 'sale':
                line.product_updatable = False


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _compute_show_project_and_task_button(self):
        is_project_manager = self.env.user.has_group('project.group_project_manager')
        show_button_ids = self.env['sale.order.line']._read_group([
            ('order_id', 'in', self.ids),
            ('order_id.state', 'not in', ['draft', 'sent']),
            ('product_id.detailed_type', 'in', ('service', 'product')),
        ], aggregates=['order_id:array_agg'])[0][0]
        for order in self:
            order.show_project_button = order.id in show_button_ids and order.project_count
            order.show_task_button = order.show_project_button or order.tasks_count
            order.show_create_project_button = is_project_manager and order.id in show_button_ids and not order.project_count and order.order_line.product_template_id.filtered(
                lambda x: x.service_policy in ['delivered_timesheet', 'delivered_milestones'])

    def action_create_project(self):
        self.ensure_one()
        if not self.order_line:
            return {'type': 'ir.actions.act_window_close'}

        sorted_line = self.order_line.sorted('sequence')
        default_sale_line = next(sol for sol in sorted_line if sol.product_id.detailed_type in ('service', 'product'))
        res = {
            **self.env["ir.actions.actions"]._for_xml_id("project.open_create_project"),
            'context': {
                'default_sale_order_id': self.id,
                'default_sale_line_id': default_sale_line.id,
                'default_partner_id': self.partner_id.id,
                'default_user_ids': [self.env.uid],
                'default_allow_billable': 1,
                'hide_allow_billable': True,
                'default_company_id': self.company_id.id,
                'generate_milestone': default_sale_line.product_id.service_policy == 'delivered_milestones',
            },
        }
        return res

    def action_view_project_ids(self):
        self.ensure_one()
        if not self.order_line:
            return {'type': 'ir.actions.act_window_close'}

        sorted_line = self.order_line.sorted('sequence')
        default_sale_line = next(sol for sol in sorted_line if sol.product_id.detailed_type in ('service', 'product'))
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Projects'),
            'domain': ['|', ('sale_order_id', '=', self.id),
                       ('id', 'in', self.with_context(active_test=False).project_ids.ids),
                       ('active', 'in', [True, False])],
            'res_model': 'project.project',
            'views': [(False, 'kanban'), (False, 'tree'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'context': {
                **self._context,
                'default_partner_id': self.partner_id.id,
                'default_sale_line_id': default_sale_line.id,
                'default_allow_billable': 1,
            }
        }
        if len(self.with_context(active_test=False).project_ids) == 1:
            action.update({'views': [(False, 'form')], 'res_id': self.project_ids.id})
        return action

    def action_confirm(self):
        self = self.with_context(contract_id=self.contract_id.id, analytic_account_id=self.analytic_account_id.id)
        res = super().action_confirm()
        return res

    def action_view_task(self):
        self.ensure_one()
        if not self.order_line:
            return {'type': 'ir.actions.act_window_close'}

        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id
        kanban_view_id = self.env.ref('project.view_task_kanban_inherit_view_default_project').id

        action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_task")
        if self.tasks_count > 1:  # cross project kanban task
            for idx, (view_id, view_type) in enumerate(action['views']):
                if view_type == 'kanban':
                    action['views'][idx] = (kanban_view_id, 'kanban')
                elif view_type == 'tree':
                    action['views'][idx] = (list_view_id, 'tree')
                elif view_type == 'form':
                    action['views'][idx] = (form_view_id, 'form')
        else:  # 1 or 0 tasks -> form view
            action['views'] = [(form_view_id, 'form')]
            action['res_id'] = self.tasks_ids.id
        # set default project
        default_line = next((sol for sol in self.order_line if sol.product_id.detailed_type in ('service', 'product')),
                            self.env['sale.order.line'])
        default_project_id = default_line.project_id.id or self.project_id.id or self.project_ids[
                                                                                 :1].id or self.tasks_ids.project_id[
                                                                                           :1].id

        action['context'] = {
            'default_sale_order_id': self.id,
            'default_sale_line_id': default_line.id,
            'default_partner_id': self.partner_id.id,
            'default_project_id': default_project_id,
            'default_user_ids': [self.env.uid],
        }
        action['domain'] = AND([ast.literal_eval(action['domain']), [('id', 'in', self.tasks_ids.ids)]])
        return action


