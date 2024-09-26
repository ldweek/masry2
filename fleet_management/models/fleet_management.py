from odoo import models, fields, api, _
from datetime import timedelta, datetime


def _get_float_from_time(time):
    time_delta = timedelta(hours=time)
    datetime_time = datetime(1, 1, 1) + time_delta
    str_time = datetime_time.strftime("%H:%M")
    return str_time


class FleetManagement(models.Model):
    _name = 'fleet.management'

    name = fields.Char()
    date = fields.Date()
    day = fields.Selection([('Sunday', 'Sunday'), ('Monday', 'Monday'),
                            ('Tuesday', 'Tuesday'),
                            ('Wednesday', 'Wednesday'),
                            ('Thursday', 'Thursday'),
                            ('Friday', 'Friday'),
                            ('Saturday', 'Saturday'),
                            ])
    partner_id = fields.Many2one('res.partner')
    contract_ids = fields.One2many('contract.contract', compute='get_contract_ids')

    driver_id = fields.Many2one('hr.employee')
    driver_phone = fields.Char(related='driver_id.work_phone')
    car_id = fields.Many2one('fleet.vehicle')
    car_number = fields.Char(related='car_id.license_plate')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', related='car_id.model_id')
    car_type = fields.Selection([('microbus', 'Microbus'),
                                 ('private_vehicle', 'private vehicle'),
                                 ('van', 'Van'),
                                 ('tank_transport', 'Tank transport'),
                                 ('jumbo_transport', 'Jumbo transport')],
                                required=True)
    vehicle_dependence = fields.Selection([('rent', 'Rent'), ('Ownership', 'Ownership')])
    car_active = fields.Selection([('combinations', 'Combinations'), ('examinations', 'Examinations')])
    line_ids = fields.One2many('fleet.line', 'management_id')
    movement_ids = fields.One2many('fleet.movement.line', 'management_id')
    total_movement = fields.Float('Total', compute='compute_movement', store=True)
    total_expense = fields.Float('Total', compute='compute_expenses', store=True)

    def get_contract_ids(self):
        ids = []
        self.contract_ids = False
        for line in self.movement_ids:
            ids.append(line.contract_id.id)
        self.contract_ids = ids

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('fleet.management.seq') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids', 'line_ids.expenses', 'line_ids.state')
    def compute_expenses(self):
        total = 0.0
        for line in self.line_ids.filtered(lambda check: check.state == 'accepted'):
            total += line.expenses
        self.total_expense = total

    @api.depends('movement_ids', 'movement_ids.total_cost', 'movement_ids.Kilometers_movement',
                 'movement_ids.cost_liter_gasoline',
                 'movement_ids.liters_gasoline', 'movement_ids.meter_before_move', 'movement_ids.meter_after_move',
                 )
    def compute_movement(self):
        self.total_movement = sum(line.total_cost for line in self.movement_ids)


class FleetLine(models.Model):
    _name = 'fleet.line'

    management_id = fields.Many2one('fleet.management')
    expense_id = fields.Many2one('fleet.expenses')
    expenses = fields.Float()
    state = fields.Selection([('accepted', 'Accepted'), ('refused', 'Refused'), ('draft', 'Draft')], default='draft')

    def do_accept(self):
        self.state = 'accepted'

    def do_refuse(self):
        self.state = 'refused'

    def set_to_draft(self):
        self.state = 'draft'


class FleetMovement(models.Model):
    _name = 'fleet.movement.line'

    contract_id = fields.Many2one('contract.contract')
    analytic_account_id = fields.Many2one('account.analytic.account',related='contract_id.analytic_account_id',
                                          string='Analytic Account')
    management_id = fields.Many2one('fleet.management')
    meter_before_move = fields.Integer(help='Reading the meter at the start of movement')
    meter_after_move = fields.Integer(help='Reading the meter at the end of movement')
    starting_point = fields.Many2one('res.city')
    destination_address = fields.Many2one('res.city')
    time_movement = fields.Float(string="Time Movement")
    time_arrival = fields.Float(string="Time Arrival")
    duration_movement = fields.Float(compute='_compute_duration', readonly=True)
    Kilometers_movement = fields.Integer(compute='_compute_Kilometers_and_gasoline', readonly=True)
    liters_gasoline = fields.Float(compute='_compute_Kilometers_and_gasoline', readonly=True)
    cost_liter_gasoline = fields.Float()
    cost_movement = fields.Float(compute='compute_cost_movement', readonly=True, store=True)
    total_cost = fields.Float(compute='_compute_total_cost')

    @api.onchange('management_id.car_type', 'meter_after_move', 'meter_before_move')
    def _compute_Kilometers_and_gasoline(self):
        for rec in self:
            rec.Kilometers_movement = False
            rec.liters_gasoline = False
            if rec.meter_after_move and rec.meter_before_move:
                kilometers = rec.meter_after_move - rec.meter_before_move
                rec.Kilometers_movement = kilometers
                if rec.management_id.car_type == 'microbus':
                    rec.liters_gasoline = kilometers / 7
                elif rec.management_id.car_type == 'private_vehicle':
                    rec.liters_gasoline = kilometers / 5
                elif rec.management_id.car_type == 'van':
                    rec.liters_gasoline = kilometers / 5
                elif rec.management_id.car_type == 'tank_transport':
                    rec.liters_gasoline = kilometers / 10
                elif rec.management_id.car_type == 'jumbo_transport':
                    rec.liters_gasoline = kilometers / 13

    @api.depends('Kilometers_movement', 'cost_liter_gasoline', 'meter_before_move', 'meter_after_move',
                 'liters_gasoline')
    @api.onchange('Kilometers_movement', 'cost_liter_gasoline', 'meter_before_move', 'meter_after_move',
                  'liters_gasoline')
    def compute_cost_movement(self):
        for rec in self:
            rec.cost_movement = False
            if rec.Kilometers_movement and rec.cost_liter_gasoline:
                rec.cost_movement = rec.liters_gasoline * rec.cost_liter_gasoline

    @api.depends('cost_movement', 'Kilometers_movement', 'cost_liter_gasoline', 'meter_before_move', 'meter_after_move',
                 'liters_gasoline')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.cost_movement + rec.total_cost

    @api.onchange('time_movement', 'time_arrival')
    def _compute_duration(self):
        for rec in self:
            rec.duration_movement = False
            if rec.time_movement and rec.time_arrival:
                duration = rec.time_arrival - rec.time_movement
                rec.duration_movement = duration
