from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    opportunity_id = fields.Many2one('crm.lead')
    contract_id = fields.Many2one('contract.contract', compute='get_contract_id', force_save=1, store=True)

    @api.depends('opportunity_id', 'opportunity_id.contract_id')
    def get_contract_id(self):
        for record in self.filtered(lambda r: not r.contract_id and r.opportunity_id):
            record.contract_id = record.opportunity_id.contract_id


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    is_payment = fields.Boolean()
    can_create_contract = fields.Boolean()


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    is_payment = fields.Boolean(related='stage_id.is_payment')
    can_create_contract = fields.Boolean(related='stage_id.can_create_contract')
    inspection_fees = fields.Float()
    is_paid = fields.Boolean()
    employee_id = fields.Many2one('hr.employee', string='Employee', required=False)
    assign_to = fields.Many2one('hr.employee', string='Assign To', required=True)
    inspection_exit_date = fields.Datetime()
    inspection_delivery_date = fields.Datetime()
    shift = fields.Selection([('am', 'am'), ('pm', 'pm')])
    way_id = fields.Many2one('way', )
    customer_type_id = fields.Many2one('customer.type', )
    line_ids = fields.One2many('crm.lead.line', 'lead_id')
    count_payment = fields.Integer(compute='compute_count_payment')
    contract_id = fields.Many2one('contract.contract')
    inspection_receiver = fields.Many2one('hr.employee')
    is_created_contract = fields.Boolean(default=False, copy=False)
    street = fields.Char(related='partner_id.street' ,readonly=False ,string='Address')




    def compute_count_payment(self):
        for rec in self:
            rec.count_payment = self.env['account.payment'].search_count([('opportunity_id', '=', self.id)])

    def action_open_payment(self):
        self.ensure_one()
        payment = self.env['account.payment'].search([('opportunity_id', '=', self.id)])
        self.ensure_one()

        action = {
            'name': _("Paid Opportunity"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payment) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payment.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', payment.ids)],
            })
        return action

    def action_sale_quotations_new(self):
        vals = {
            'opportunity_id': self.id,
            'partner_id': self.partner_id.id,
            'contract_id': self.contract_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'origin': self.name,
            'source_id': self.source_id.id,
            'company_id': self.company_id.id or self.env.company.id,
            'tag_ids': [(6, 0, self.tag_ids.ids)]
        }
        if self.team_id:
            vals['team_id'] = self.team_id.id
        if self.user_id:
            vals['user_id'] = self.user_id.id

        sale_id = self.env['sale.order'].create(vals)
        self.create_sale_line(sale_id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Quotation',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': sale_id.id,
            'target': 'current',
        }

    def create_sale_line(self, sale_id):
        for line in self.line_ids:
            sale_line = self.env['sale.order.line']
            sale_line.create({
                'product_id': line.product_id.id,
                'product_uom_qty': 1,
                'tall': line.tall,
                'width': line.width,
                'height': line.height,
                'price_unit': line.total,
                'order_id': sale_id.id,
            })

    def action_payment(self):
        payment = self.env['account.payment'].create({
            'partner_id': self.partner_id.id,
            'opportunity_id': self.id,
            'amount': self.inspection_fees,
        })
        self.is_paid = True
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': payment.id,
            'target': 'current',
        }

    def _prepare_vals_contract(self):
        vals = {
            'partner_id': self.partner_id.id,
            'start_date': fields.date.today(),
            'contract_date': fields.date.today(),
            'opportunity_id': self.id,
        }
        return vals

    def _create_contract(self):
        vals = self._prepare_vals_contract()
        res = self.env['contract.contract'].create(vals)
        return res

    def create_contract(self):
        self.ensure_one()
        res = self._create_contract()
        self.contract_id = res.id
        self.is_created_contract = True
        return {
                'name': _('Create Contract'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_id': res.id,
                'res_model': 'contract.contract',
                'target': 'current',
            }



class CrmLeadLine(models.Model):
    _name = 'crm.lead.line'

    product_id = fields.Many2one('product.product')
    quantity = fields.Float()
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict')
    lead_id = fields.Many2one('crm.lead')
    unit_price = fields.Float(compute='compute_unit_price', store=True, string='Price')

    @api.depends('product_id')
    def _compute_product_uom(self):
        for line in self:
            if not line.product_uom or (line.product_id.uom_id.id != line.product_uom.id):
                line.product_uom = line.product_id.uom_id

    @api.depends('product_id')
    def compute_unit_price(self):
        for line in self:
            if not line.unit_price:
                line.unit_price = line.product_id.list_price
