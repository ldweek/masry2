# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


def calculate(v1, v2, operator):
    if operator == "-":
        return v1 - v2
    elif operator == "+":
        return v1 + v2
    elif operator == "*":
        return v1 * v2
    elif operator == "/":
        return v1 / v2
    else:
        return "Invalid operator"


class EquationEquation(models.Model):
    _name = 'equation.equation'

    name = fields.Char('Name', required=True)

    var_1 = fields.Selection([
        ('tall', 'Tall'),
        ('width', 'Width'),
        ('height', 'Height')
    ], required=True)

    operator_r1 = fields.Selection([
        ('-', '-'),
        ('+', '+'),
        ('*', '*'),
        ('/', '/'),
    ], 'Operator', required=True)

    var_2 = fields.Selection([
        ('tall', 'Tall'),
        ('width', 'Width'),
        ('height', 'Height')
    ], required=True)

    operator_r2 = fields.Selection([
        ('-', '-'),
        ('+', '+'),
        ('*', '*'),
        ('/', '/'),
    ], 'Operator')

    var_3 = fields.Selection([
        ('tall', 'Tall'),
        ('width', 'Width'),
        ('height', 'Height')
    ])

    operator_r3 = fields.Selection([
        ('-', '-'),
        ('+', '+'),
        ('*', '*'),
        ('/', '/'),
    ], 'Operator')

    var_4 = fields.Float('Fixed Value')

    def calculate_result(self, bom_id):
        eq_fields = ['var_1', 'operator_r1', 'var_2', 'operator_r2', 'var_3', 'operator_r3', 'var_4']
        eq_values = self.search_read([('id', '=', self.id)], eq_fields)[0]
        pro_values = self.env['mrp.bom'].search_read([('id', '=', bom_id.id)], ['tall', 'width', 'height'])[0]
        result = calculate(pro_values[eq_values[eq_fields[0]]] or 0, pro_values[eq_values[eq_fields[2]]] or 0,
                           eq_values[eq_fields[1]])
        if eq_values[eq_fields[3]]:
            result = calculate(result or 0, pro_values[eq_values[eq_fields[4]]] or 0, eq_values[eq_fields[3]])
        if eq_values[eq_fields[5]]:
            result = calculate(result or 0, eq_values[eq_fields[6]] or 0, eq_values[eq_fields[5]])
        return result

    def calculate_result_1(self, tall=0, width=0, height=0):
        eq_fields = ['var_1', 'operator_r1', 'var_2', 'operator_r2', 'var_3', 'operator_r3', 'var_4']
        eq_values = self.search_read([('id', '=', self.id)], eq_fields)[0]
        pro_values = {
            'tall': tall,
            'width': width,
            'height': height,
        }
        result = calculate(pro_values[eq_values[eq_fields[0]]] or 0, pro_values[eq_values[eq_fields[2]]] or 0,
                           eq_values[eq_fields[1]])
        if eq_values[eq_fields[3]]:
            result = calculate(result or 0, pro_values[eq_values[eq_fields[4]]] or 0, eq_values[eq_fields[3]])
        if eq_values[eq_fields[5]]:
            result = calculate(result or 0, eq_values[eq_fields[6]] or 0, eq_values[eq_fields[5]])
        return result
