from odoo.exceptions import UserError
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)



class Distortion(models.Model):
    _name = 'distortion.order'

    name = fields.Char(required=True, copy=False)
    contract_id = fields.Many2one('contract.contract')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    partner_id = fields.Many2one('res.partner')
    installation_manger_id = fields.Many2one('hr.employee', string='Installation Manger')
    request_distortion_date = fields.Date('Request Date', default=lambda self: fields.Date.today(), readonly=1)
    line_ids = fields.One2many('distortion.order.line', 'distortion_id')
    total_amount = fields.Float(compute='_compute_total_amount', store=True)

    @api.onchange('line_ids', 'line_ids.amount_distortion')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(line.amount_distortion for line in record.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('distortion.seq') or _('New')
        return super().create(vals_list)


class DistortionLine(models.Model):
    _name = 'distortion.order.line'

    product_id = fields.Many2one('product.product', domain=lambda self: self._get_product_id_domain())
    distortion_id = fields.Many2one('distortion.order')
    type_distortion = fields.Many2one('type.distortion', )
    floor_count = fields.Many2one('type.distortion.line',
                                  requierd=True, domain="[('type_distortion_id', '=', type_distortion)]")
    amount_bonus = fields.Float(related='floor_count.amount')
    meters = fields.Float()
    receiving_paper = fields.Many2one('receiving.paper')
    signature = fields.Many2one('signature')
    photo = fields.Binary(attachment=True, required=True)
    notes_photo_video = fields.Text()
    date_photo_receiving = fields.Date()
    amount_distortion = fields.Float(string='Total', compute='_compute_total' , store=True, force_save=1)
    quantity = fields.Float()

    @api.onchange('meters', 'amount_bonus')
    def _compute_total(self):
        for line in self:
            line.amount_distortion = 0.0
            if line.amount_bonus:
                line.amount_distortion = line.amount_bonus * line.meters

            # bonus_floors = {
            #     'ground': line.env['ir.config_parameter'].sudo().get_param('floor_ground'),
            #     '1': line.env['ir.config_parameter'].sudo().get_param('floor_1'),
            #     '2': line.env['ir.config_parameter'].sudo().get_param('floor_2'),
            #     '3': line.env['ir.config_parameter'].sudo().get_param('floor_3'),
            #     '4': line.env['ir.config_parameter'].sudo().get_param('floor_4'),
            #     '5_7': line.env['ir.config_parameter'].sudo().get_param('floor_5_to_7'),
            #     '8_and_above': line.env['ir.config_parameter'].sudo().get_param('floor_8'),
            # }

            # bonus_floor = bonus_floors.get(line.floor_count, 0.0)
            # line.amount_distortion = amount_distortion * float(bonus_floor)

    @api.depends('distortion_id.contract_id')
    def _get_product_id_domain(self):
        for rec in self:
            contract_id = rec.distortion_id.contract_id
            if contract_id:
                sale_ids = self.env['sale.order'].search([('contract_id', '=', contract_id.id)])
                product_ids = sale_ids.mapped('order_line').mapped('product_id').ids
                return [('id', 'in', product_ids)]
            return []

    @api.constrains('photo')
    def check_photo(self):
        for record in self:
            if not record.photo:
                raise UserError(_('Please, attach a photo for this distortion order.'))
#