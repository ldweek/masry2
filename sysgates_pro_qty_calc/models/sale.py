from datetime import timedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    state_item = fields.Selection(
        [('in-progress', 'In Progress'), ('pause', 'Pause'), ('delay', 'Delay'), ('done', 'Done')],
        default='in-progress', readonly=True)
    state_installation = fields.Selection([('completed', 'Completed'), ('uncompleted', 'Uncompleted')],
                                          default='uncompleted', readonly=True,
                                          compute='get_state_installation', store=True)
    start_date = fields.Date(default=lambda s: s.contract_id.start_date, compute='compute_start_date', store=True)
    qty_distorted = fields.Float()
    available_qty_to_distort = fields.Float(compute='compute_available_qty_to_distort')
    reason_pause = fields.Text(force_save=1)
    attachment_pause = fields.Binary(attachment=True, force_save=1)
    attachment_resume = fields.Binary(attachment=True, force_save=1)
    is_pause = fields.Boolean(default=False)
    is_resumed = fields.Boolean(default=False)

    @api.onchange('qty_distorted', 'available_qty_to_distort', 'product_uom_qty')
    @api.depends('qty_distorted', 'available_qty_to_distort', 'product_uom_qty')
    def get_state_installation(self):
        for rec in self:
            rec.state_installation = 'uncompleted'
            if rec.qty_distorted >= rec.product_uom_qty:
                rec.state_installation = 'completed'
                rec.state_item = 'done'

    @api.depends('product_uom_qty', 'qty_distorted')
    @api.onchange('product_uom_qty', 'qty_distorted')
    def compute_available_qty_to_distort(self):
        for rec in self:
            rec.available_qty_to_distort = rec.product_uom_qty - rec.qty_distorted

    @api.depends('contract_id', 'contract_id.start_date')
    def compute_start_date(self):
        for line in self:
            if line.start_date and line.start_date != line.contract_id.start_date:
                continue

            elif not line.start_date and line.contract_id and line.contract_id.start_date:
                line.start_date = line.contract_id.start_date

            elif not line.start_date and not line.contract_id:
                line.start_date = False

    def pause_installation(self):
        for line in self:
            if not line.attachment_pause or not line.reason_pause:
                print(not line.attachment_pause, not line.reason_pause)
                print(line.attachment_pause, line.reason_pause, line.product_id.name)
                raise UserError(_('Please upload both the pause attachment and the reason for pausing.'))
            line.state_item = 'pause'
            line.is_pause = True

    def resume_installation(self):
        for line in self:
            if not line.attachment_resume:
                raise UserError(_('Please upload the resume attachment.'))
            line.state_item = 'in-progress'
            line.start_date = fields.Date.today()
            line.is_resumed = True

    def installation_is_done(self):
        for line in self:
            config_day = int(self.env['ir.config_parameter'].get_param('day_installation'))
            if line.start_date:
                finished_day = line.start_date + timedelta(days=config_day)
                if finished_day < fields.Date.today() and line.state_item == 'in-progress':
                    line.state_item = 'delay'
