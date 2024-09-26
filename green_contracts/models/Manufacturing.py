from odoo.tools import float_compare
from odoo import api, fields, models, _


class ManufacturingDepartment(models.Model):
    _name = 'manufacturing.department'
    _order = 'id desc'


    contract_id = fields.Many2one(
        comodel_name='contract.contract',
        string="Contract Reference",
        required=True, ondelete='cascade', copy=False)

    code = fields.Char(related='product_id.default_code', readonly=True)

    # contract-related fields
    company_id = fields.Many2one(
        related='contract_id.company_id',
        store=True, precompute=True)
    currency_id = fields.Many2one(
        related='contract_id.currency_id',
        depends=['contract_id.currency_id'],
        store=True, precompute=True)

    contract_partner_id = fields.Many2one(
        related='contract_id.partner_id',
        string="Customer",
        store=True, precompute=True)

    state = fields.Selection(
        related='contract_id.state',
        string="Contract Status",
        copy=False, store=True, precompute=True)

    # Fields specifying custom line logic
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)

    # Generic configuration fields
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        change_default=True, ondelete='restrict', index='btree_not_null',
        domain="[('sale_ok', '=', True)]")
    product_template_id = fields.Many2one(
        string="Product Template",
        comodel_name='product.template',
        compute='_compute_product_template_id',
        readonly=False,
        search='_search_product_template_id',
        domain=[('sale_ok', '=', True)])
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', depends=['product_id'])

    product_no_variant_attribute_value_ids = fields.Many2many(
        comodel_name='product.template.attribute.value',
        string="Extra Values",
        compute='_compute_no_variant_attribute_values',
        store=True, readonly=False, precompute=True, ondelete='restrict')

    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, required=True, precompute=True)

    product_uom_qty = fields.Float(
        string="Quantity",
        compute='_compute_product_uom_qty',
        digits='Product Unit of Measure', default=1.0,
        store=True, readonly=False, required=True, precompute=True)
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict',
        domain="[('category_id', '=', product_uom_category_id)]")
    product_packaging_id = fields.Many2one(
        comodel_name='product.packaging',
        string="Packaging",
        compute='_compute_product_packaging_id',
        store=True, readonly=False, precompute=True,
        domain="[('sales', '=', True), ('product_id','=',product_id)]",
        check_company=True)
    product_updatable = fields.Boolean(
        string="Can Edit Product",
        compute='_compute_product_updatable')

    product_packaging_qty = fields.Float(
        string="Packaging Quantity",
        compute='_compute_product_packaging_qty',
        store=True, readonly=False, precompute=True)
    product_type = fields.Selection(related='product_id.detailed_type', depends=['product_id'])

    discount = fields.Float(
        string="Discount (%)",
        compute='_compute_discount',
        digits='Discount',
        store=True, readonly=False, precompute=True)

    price_subtotal = fields.Monetary(
        string="Subtotal",
        compute='_compute_amount',
        store=True, precompute=True)
    price_tax = fields.Float(
        string="Total Tax",
        compute='_compute_amount',
        store=True, precompute=True)
    price_total = fields.Monetary(
        string="Total",
        compute='_compute_amount',
        store=True, precompute=True)

    tech_office_line_id = fields.Many2one('technical.office', ondelete='restrict')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    qty_done = fields.Float()
    qty_remain = fields.Float(compute='_compute_qty_remain')
    manufacturing_count = fields.Integer(compute='_compute_count')
    material_request_count = fields.Integer(compute='_compute_count')
    stock_count = fields.Integer(compute='_compute_count')

    def open_request_wizad(self):
        action = self.env.ref('green_contracts.supply_chain_wizard_action_id')
        product_and_qty = {product.product_id.id: product.product_uom_qty for product in self}
        vals = []
        for rec in self:
            vals.append((0, 0, {
                'product_id': rec.product_id.id,
                'quantity': rec.qty_remain,
                'record_id': rec.id,
                'unit_id': rec.product_uom.id,
                'record_name': rec.name,
                'contract_id': rec.contract_id.id,
            }))

        result = {
            'name': action.name,
            'type': 'ir.actions.act_window',
            'res_model': action.res_model,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_line_ids': vals,
                'product_and_qty': product_and_qty
            }
        }
        return result

    def open_material_request_action(self):
        self.ensure_one()
        action = {
            'name': _("Material Request list"),
            'type': 'ir.actions.act_window',
            'res_model': 'material.request',
            'context': {'create': False},
        }

        ref = f'{self._name},{self.id}'
        material_request_id = self.env['material.request'].search([('ref', '=', ref)])

        if len(material_request_id) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': material_request_id.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', material_request_id.ids)],
            })
        return action

    def open_manufacturing_action(self):
        self.ensure_one()
        action = {
            'name': _("Manufacturing request list"),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'context': {'create': False},
        }
        ref = f'{self._name},{self.id}'
        manufacturing_id = self.env['mrp.production'].search([('ref', '=', ref)])

        if len(manufacturing_id) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': manufacturing_id.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', manufacturing_id.ids)],
            })
        return action

    def open_stock_picking_action(self):
        self.ensure_one()
        action = {
            'name': _("stock request list"),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'context': {'create': False},
        }
        ref = f'{self._name},{self.id}'
        stock_id = self.env['stock.picking'].search([('ref', '=', ref)])

        if len(stock_id) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': stock_id.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', stock_id.ids)],
            })
        return action

    def _compute_count(self):
        for line in self:
            ref = f'{line._name},{line.id}'
            line.material_request_count = self.env['material.request'].search_count([('ref', '=', ref)])
            line.stock_count = self.env['stock.picking'].search_count([('ref', '=', ref)])
            line.manufacturing_count = self.env['mrp.production'].search_count([('ref', '=', ref)])

    def _compute_qty_remain(self):
        for rec in self:
            rec.qty_remain = rec.product_uom_qty - rec.qty_done

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id

    @api.depends('product_id')
    def _compute_no_variant_attribute_values(self):
        for line in self:
            if not line.product_id:
                line.product_no_variant_attribute_value_ids = False
                continue
            if not line.product_no_variant_attribute_value_ids:
                continue
            valid_values = line.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
            # remove the no_variant attributes that don't belong to this template
            for ptav in line.product_no_variant_attribute_value_ids:
                if ptav._origin not in valid_values:
                    line.product_no_variant_attribute_value_ids -= ptav

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                continue
            lang = line.contract_id._get_lang()
            if lang != self.env.lang:
                line = line.with_context(lang=lang)
            name = f'{line.contract_id.name} - {line.product_id.name}'
            line.name = name

    @api.depends('product_id', 'product_uom_qty', 'product_uom')
    def _compute_product_packaging_id(self):
        for line in self:
            # remove packaging if not match the product
            if line.product_packaging_id.product_id != line.product_id:
                line.product_packaging_id = False
            # suggest biggest suitable packaging matching the SO's company
            if line.product_id and line.product_uom_qty and line.product_uom:
                suggested_packaging = line.product_id.packaging_ids \
                    .filtered(lambda p: p.sales and (p.product_id.company_id <= p.company_id <= line.company_id)) \
                    ._find_suitable_product_packaging(line.product_uom_qty, line.product_uom)
                line.product_packaging_id = suggested_packaging or line.product_packaging_id

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_discount(self):
        for line in self:
            if not line.product_id or line.display_type:
                line.discount = 0.0

            if not (
                    line.contract_id.pricelist_id
                    and line.contract_id.pricelist_id.discount_policy == 'without_discount'
            ):
                continue

            line.discount = 0.0

            if not line.pricelist_item_id:
                # No pricelist rule was found for the product
                # therefore, the pricelist didn't apply any discount/change
                # to the existing sales price.
                continue

            line = line.with_company(line.company_id)
            pricelist_price = line._get_pricelist_price()
            base_price = line._get_pricelist_price_before_discount()

            if base_price != 0:  # Avoid division by zero
                discount = (base_price - pricelist_price) / base_price * 100
                if (discount > 0 and base_price > 0) or (discount < 0 and base_price < 0):
                    # only show negative discounts if price is negative
                    # otherwise it's a surcharge which shouldn't be shown to the customer
                    line.discount = discount

    @api.depends('display_type', 'product_id', 'product_packaging_qty')
    def _compute_product_uom_qty(self):
        for line in self:
            if line.display_type:
                line.product_uom_qty = 0.0
                continue

            if not line.product_packaging_id:
                continue
            packaging_uom = line.product_packaging_id.product_uom_id
            qty_per_packaging = line.product_packaging_id.qty
            product_uom_qty = packaging_uom._compute_quantity(
                line.product_packaging_qty * qty_per_packaging, line.product_uom)
            if float_compare(product_uom_qty, line.product_uom_qty,
                             precision_rounding=line.product_uom.rounding) != 0:
                line.product_uom_qty = product_uom_qty

    @api.depends('product_id')
    def _compute_custom_attribute_values(self):
        for line in self:
            if not line.product_id:
                line.product_custom_attribute_value_ids = False
                continue
            if not line.product_custom_attribute_value_ids:
                continue
            valid_values = line.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
            # remove the is_custom values that don't belong to this template
            for pacv in line.product_custom_attribute_value_ids:
                if pacv.custom_product_template_attribute_value_id not in valid_values:
                    line.product_custom_attribute_value_ids -= pacv

    @api.depends('product_packaging_id', 'product_uom', 'product_uom_qty')
    def _compute_product_packaging_qty(self):
        self.product_packaging_qty = 0
        for line in self:
            if not line.product_packaging_id:
                continue
            line.product_packaging_qty = line.product_packaging_id._compute_qty(line.product_uom_qty,
                                                                                line.product_uom)

    @api.depends('product_id', 'state')
    def _compute_product_updatable(self):
        for line in self:
            if line.state == 'cancel':
                line.product_updatable = False
            elif line.state == 'confirmed' and (
                    line.contract_id.locked

            ):
                line.product_updatable = False
            else:
                line.product_updatable = True

    @api.depends('product_uom_qty', 'discount', )
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            tax_results = self.env['account.tax'].with_company(line.company_id)._compute_taxes([
                line._convert_to_tax_base_line_dict()
            ])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })

    @api.depends('product_id')
    def _compute_product_uom(self):
        for move in self:
            move.product_uom = move.product_id.uom_id.id

    def _convert_to_tax_base_line_dict(self, **kwargs):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.contract_id.partner_id,
            currency=self.contract_id.currency_id,
            product=self.product_id,
            quantity=self.product_uom_qty,
            discount=self.discount,
            price_subtotal=self.price_subtotal,
            **kwargs, )
