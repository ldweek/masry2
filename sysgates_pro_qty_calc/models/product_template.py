# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    equation_id = fields.Many2one('equation.equation', 'Equation')
