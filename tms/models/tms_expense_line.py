# -*- coding: utf-8 -*-
# © <2012> <Israel Cruz Argil, Argil Consulting>
# © <2016> <Jarsa Sistemas, S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import _, api, fields, models
from openerp.exceptions import ValidationError


class TmsExpenseLine(models.Model):
    _name = 'tms.expense.line'
    _description = 'Expense Line'

    travel_id = fields.Many2one(
        'tms.travel',
        string='Travel',
        required=True)
    expense_id = fields.Many2one(
        'tms.expense',
        string='Expense',
        readonly=True)
    product_qty = fields.Float(
        string='Qty (UoM)')
    unit_price = fields.Float()
    price_subtotal = fields.Float(
        compute='_compute_price_subtotal',
        string='Subtotal',)
    product_uom_id = fields.Many2one(
        'product.uom',
        string='Unit of Measure')
    line_type = fields.Selection(
        [('real_expense', 'Real Expense'),
         ('madeup_expense', 'Made-up Expense'),
         ('salary', 'Salary'),
         ('fuel', 'Fuel'),
         ('salary_retention', 'Salary Retention'),
         ('salary_discount', 'Salary Discount'),
         ('negative_balance', 'Negative Balance')],
        default='real_expense')
    name = fields.Char(
        'Description',
        required=True)
    sequence = fields.Integer(
        help="Gives the sequence order when displaying a list of "
        "sales order lines.",
        default=10)
    price_total = fields.Float(
        string='Total',
        compute='_compute_price_total',
        )
    tax_amount = fields.Float(
        compute='_compute_tax_amount',)
    special_tax_amount = fields.Float(
        string='Special Tax'
        )
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        domain=[('type_tax_use', '=', 'purchase')])
    notes = fields.Text()
    employee_id = fields.Many2one(
        'hr.employee',
        string='Driver')
    date = fields.Date(readonly=True)
    state = fields.Char(readonly=True)
    fuel_voucher = fields.Boolean()
    control = fields.Boolean('Control')
    automatic = fields.Boolean(
        help="Check this if you want to create Advances and/or "
        "Fuel Vouchers for this line automatically")
    credit = fields.Boolean(
        help="Check this if you want to create Fuel Vouchers for "
        "this line")
    is_invoice = fields.Boolean(string='Is Invoice?')
    partner_id = fields.Many2one('res.partner', string='Supplier')
    invoice_date = fields.Date('Date')
    invoice_number = fields.Char()
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Supplier Invoice')
    product_id = fields.Many2one(
        'product.product',
        domain=[('type', '=', 'service'),
                ('purchase_ok', '=', 'True')],
        string='Product')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.tax_ids = self.product_id.supplier_taxes_id
        self.product_uom_id = self.product_id.uom_id.id

    @api.depends('tax_ids', 'product_qty', 'unit_price')
    def _compute_tax_amount(self):
        for rec in self:
            taxes = rec.tax_ids.compute_all(
                rec.unit_price, rec.expense_id.currency_id,
                rec.product_qty,
                rec.expense_id.employee_id.address_home_id)
            if taxes:
                for tax in taxes['taxes']:
                    rec.tax_amount += tax['amount']
            else:
                rec.tax_amount = 0.0

    @api.depends('product_qty', 'unit_price')
    def _compute_price_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.product_qty * rec.unit_price

    @api.depends('price_subtotal')
    def _compute_price_total(self):
        for rec in self:
            rec.price_total = rec.price_subtotal + rec.tax_amount

    @api.model
    def create(self, values):
        expense_line = super(TmsExpenseLine, self).create(values)
        if expense_line.line_type in ('salary_discount', 'negative_balance'):
            if expense_line.price_total > 0:
                raise ValidationError(_('This line type needs a '
                                        'negative value to continue!'))
        return expense_line
