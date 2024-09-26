from odoo import models, fields, api


class TypeDistortion(models.Model):
    _name = 'type.distortion'

    name = fields.Char(required=True)
    type_distortion_line_ids = fields.One2many('type.distortion.line', 'type_distortion_id')


class TypeDistortionLine(models.Model):
    _name = 'type.distortion.line'
    _rec_name = 'floor_no'

    type_distortion_id = fields.Many2one('type.distortion', string='Type of Distortion')
    floor_no = fields.Char(required=True)
    amount = fields.Float(required=True)


class ReceivingPaper(models.Model):
    _name = 'receiving.paper'

    name = fields.Char(required=True)


class Signature(models.Model):
    _name = 'signature'

    name = fields.Char(required=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    selected = fields.Boolean(default=False)
    available_qty_to_distort = fields.Float()
