# The COPYRIGHT file at the top level of this repository contains the full i
# copyright notices and license terms.

from trytond.model import fields
from trytond.pyson import Eval, Bool
from trytond.pool import PoolMeta
from decimal import Decimal

__all__ = ['InformationUomMixin', 'InvoiceLine']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')
_ROUND = Decimal('.0001')

STATES = {
    'invisible': ~Bool(Eval('show_info_unit')),
    }
DEPENDS = ['show_info_unit']


class InformationUomMixin:
    show_info_unit = fields.Function(fields.Boolean('Show Information UOM',
            on_change_with=['product']), 'on_change_with_show_info_unit')
    info_unit = fields.Function(fields.Many2One('product.uom',
            'Information UOM',
            on_change_with=['product'], states=STATES, depends=DEPENDS),
        'on_change_with_info_unit')
    info_unit_digits = fields.Function(fields.Integer(
        'Information Unit Digits', on_change_with=['info_unit'], states=STATES,
            depends=DEPENDS),
        'on_change_with_info_unit_digits')

    info_quantity = fields.Numeric('Information Quantity',
        digits=(16, Eval('info_unit_digits', 2)),
        states={
            'invisible': (~Bool(Eval('show_info_unit')) |
                (Eval('type') != 'line')),
            'required': (Bool(Eval('show_info_unit')) &
                (Eval('type') == 'line')),
            },
        on_change_with=['quantity', 'product', 'info_quantity',
            'info_unit_price', 'product'],
        on_change=['quantity', 'unit_quantity', 'unit',
            'info_quantity', 'info_unit_price', 'product'],
        depends=['type', 'info_unit_digits', 'product', 'unit', 'unit_digits',
            'show_info_unit'])

    info_unit_price = fields.Numeric('Information Unit Price', digits=(16, 4),
        states={
            'invisible': (~Bool(Eval('show_info_unit')) |
                (Eval('type') != 'line')),
            'required': (Bool(Eval('show_info_unit')) &
                (Eval('type') == 'line')),
            },
        on_change=['info_unit_price', 'product', 'info_quantity', 'type'],
        on_change_with=['unit_price', 'type', 'info_unit_price',
            'info_quantity', 'product', 'unit_price'],
        depends=['type', 'product'])

    info_amount = fields.Function(fields.Numeric('Information Amount',
            digits=(16, Eval('currency_digits', 2)),
            states={
                'invisible': (~Bool(Eval('show_info_unit')) |
                    ~Eval('type').in_(['line', 'subtotal'])),
                },
            on_change_with=['info_unit_price', 'info_quantity'],
            depends=['currency_digits']),
        'get_amount')

    currency_digits = fields.Function(fields.Integer('Currency Digits',
            on_change_with=[]), 'on_change_with_currency_digits')

    def on_change_with_currency_digits(self, name=None):
        return 2

    @classmethod
    def __setup__(cls):
        super(InformationUomMixin, cls).__setup__()
        for value in cls.amount.on_change_with:
            if value not in cls.info_quantity.on_change:
                cls.info_quantity.on_change.append(value)
            if value not in cls.info_unit_price.on_change:
                cls.info_unit_price.on_change.append(value)
            if value not in cls.info_amount.on_change_with:
                cls.info_amount.on_change_with.append(value)
                if not 'currency' in value:
                    cls.info_amount.depends.append(value)
        if not cls.quantity.on_change:
            cls.quantity.on_change = []
        if not cls.unit_price.on_change:
            cls.unit_price.on_change = []
        for value in cls.info_amount.on_change_with + ['product', 'quantity',
                'unit_price']:
            if value not in cls.quantity.on_change:
                cls.quantity.on_change.append(value)
            if value not in cls.unit_price.on_change:
                cls.unit_price.on_change.append(value)

    @staticmethod
    def default_info_unit_digits():
        return 2

    def on_change_with_info_unit_digits(self, name=None):
        if self.info_unit:
            return self.info_unit.digits
        return 2

    def on_change_with_show_info_unit(self, name=None):
        if self.product and self.product.use_info_unit:
            return True
        return False

    def on_change_with_info_unit(self, name=None):
        if (self.product and self.product.use_info_unit and
                self.product.info_unit):
            return self.product.info_unit.id
        return None

    def on_change_with_info_quantity(self, name=None):
        if not self.product or not self.quantity:
            return
        return self.product.calc_info_quantity(self.quantity)

    def on_change_info_quantity(self, name=None):
        if not self.product:
            return {}
        qty = self.product.calc_quantity(
                self.info_quantity, self.unit)
        self.quantity = float(qty)
        return {
            'quantity': float(qty),
            'amount':  self.on_change_with_amount(),
            }

    def on_change_with_info_unit_price(self, name=None):
        if not self.product:
            return
        if not self.unit_price:
            return
        if self.type in ('out_invoice', 'out_refund'):
            return self.product.get_info_list_price(self.unit_price)
        else:
            return self.product.get_info_cost_price(self.unit_price)

    def on_change_info_unit_price(self, name=None):
        if not self.product:
            return {}
        if not self.info_unit_price:
            return {}
        self.unit_price = self.product.get_unit_price(self.info_unit_price)
        return {
            'unit_price': self.unit_price,
            'amount': self.on_change_with_amount()
            }

    def on_change_with_info_amount(self, name=None):
        if self.info_unit_price and self.info_quantity:
            return self.info_unit_price * Decimal(str(self.info_quantity))

    def on_change_quantity(self, name=None):
        if not self.product:
            return {}
        qty = self.product.calc_info_quantity(self.quantity)
        self.info_quantity = float(qty)
        return {
            'info_quantity': float(qty),
            'info_amount':  self.on_change_with_info_amount(),
            }

    def on_change_unit_price(self, name=None):
        if not self.product:
            return {}
        if not self.unit_price:
            return {}
        self.info_unit_price = self.product.get_info_unit_price(
            self.unit_price)
        return {
            'info_unit_price': self.info_unit_price,
            'info_amount': self.on_change_with_info_amount()
            }


class InvoiceLine(InformationUomMixin):
    __name__ = 'account.invoice.line'

    @classmethod
    def __setup__(cls):
        super(InvoiceLine, cls).__setup__()
        for value in cls.amount.on_change_with:
            if value not in cls.info_quantity.on_change:
                cls.info_quantity.on_change.append(value)
            if value not in cls.info_unit_price.on_change:
                cls.info_unit_price.on_change.append(value)
        if not 'invoice' in cls.currency_digits.on_change_with:
            cls.currency_digits.on_change_with.append('invoice')
        for value in ('invoice_type',):
            if value not in cls.info_unit_price.on_change:
                cls.info_unit_price.on_change.append(value)
                cls.info_unit_price.on_change_with.append(value)
                cls.info_unit_price.depends.append(value)

    def on_change_with_currency_digits(self, name=None):
        if self.invoice:
            return self.invoice.currency_digits
        return 2
