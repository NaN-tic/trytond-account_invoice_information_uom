# The COPYRIGHT file at the top level of this repository contains the full i
# copyright notices and license terms.

from trytond.model import fields
from trytond.pyson import Eval, Bool
from trytond.pool import PoolMeta
from decimal import Decimal
from trytond.config import CONFIG
DIGITS = int(CONFIG.get('unit_price_digits', 4))

__all__ = ['InformationUomMixin', 'InvoiceLine']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')
_ROUND = Decimal('.0001')

STATES = {
    'invisible': ~Bool(Eval('show_info_unit')),
    }
DEPENDS = ['show_info_unit']


class InformationUomMixin:
    show_info_unit = fields.Function(fields.Boolean('Show Information UOM'),
        'on_change_with_show_info_unit')
    info_unit = fields.Function(fields.Many2One('product.uom',
            'Information UOM', states=STATES, depends=DEPENDS),
        'on_change_with_info_unit')
    info_unit_digits = fields.Function(fields.Integer(
        'Information Unit Digits', states=STATES, depends=DEPENDS),
        'on_change_with_info_unit_digits')
    info_quantity = fields.Float('Information Quantity',
        digits=(16, Eval('info_unit_digits', 2)),
        states={
            'invisible': (~Bool(Eval('show_info_unit')) |
                (Eval('type') != 'line')),
            'required': (Bool(Eval('show_info_unit')) &
                (Eval('type') == 'line')),
            },
        depends=['type', 'info_unit_digits', 'show_info_unit'])
    info_unit_price = fields.Numeric('Information Unit Price',
        digits=(16, DIGITS),
        states={
            'invisible': (~Bool(Eval('show_info_unit')) |
                (Eval('type') != 'line')),
            'required': (Bool(Eval('show_info_unit')) &
                (Eval('type') == 'line')),
            },
        depends=['type', 'show_info_unit'])
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')

    def on_change_with_currency_digits(self, name=None):
        return 2

    @classmethod
    def __setup__(cls):
        super(InformationUomMixin, cls).__setup__()
        for value in cls.amount.on_change_with:
            if value not in cls.info_quantity.on_change:
                cls.info_quantity.on_change.add(value)
            if value not in cls.info_unit_price.on_change:
                cls.info_unit_price.on_change.add(value)
        for value in list(cls.amount.on_change_with) + ['product', 'quantity',
                'unit_price', 'unit']:
            if value not in cls.quantity.on_change:
                cls.quantity.on_change.add(value)
            if value not in cls.unit.on_change:
                cls.unit.on_change.add(value)
            if value not in cls.unit_price.on_change:
                cls.unit_price.on_change.add(value)

    @staticmethod
    def default_info_unit_digits():
        return 2

    @fields.depends('info_unit')
    def on_change_with_info_unit_digits(self, name=None):
        if self.info_unit:
            return self.info_unit.digits
        return 2

    @fields.depends('product')
    def on_change_with_show_info_unit(self, name=None):
        if self.product and self.product.use_info_unit:
            return True
        return False

    @fields.depends('product')
    def on_change_with_info_unit(self, name=None):
        if (self.product and self.product.use_info_unit and
                self.product.info_unit):
            return self.product.info_unit.id
        return None

    @fields.depends('product', 'quantity', 'unit')
    def on_change_with_info_quantity(self, name=None):
        if not self.product or not self.quantity:
            return
        return self.product.calc_info_quantity(self.quantity, self.unit)

    @fields.depends('product', 'info_quantity', 'unit')
    def on_change_info_quantity(self, name=None):
        if not self.product:
            return {}
        qty = self.product.calc_quantity(self.info_quantity, self.unit)
        self.quantity = float(qty)
        return {
            'quantity': float(qty),
            'amount':  self.on_change_with_amount(),
            }

    @fields.depends('product', 'unit_price', 'type', 'product', 'unit')
    def on_change_with_info_unit_price(self, name=None):
        if not self.product:
            return
        if not self.unit_price:
            return self.unit_price
        if self.type in ('out_invoice', 'out_refund'):
            return self.product.get_info_list_price(self.unit_price, self.unit)
        else:
            return self.product.get_info_cost_price(self.unit_price,
                unit=self.unit)

    @fields.depends('product', 'info_unit_price', 'unit')
    def on_change_info_unit_price(self, name=None):
        if not self.product:
            return {}
        if self.info_unit_price:
            self.unit_price = self.product.get_unit_price(self.info_unit_price,
                unit=self.unit)
        else:
            self.unit_price = self.info_unit_price
        return {
            'unit_price': self.unit_price,
            'amount': self.on_change_with_amount()
            }

    @fields.depends('product', 'quantity', 'unit')
    def on_change_quantity(self, name=None):
        if not self.product:
            return {}
        qty = self.product.calc_info_quantity(self.quantity, self.unit)
        self.info_quantity = float(qty)
        return {
            'info_quantity': self.info_quantity,
            }

    @fields.depends('product', 'unit_price', 'type', 'product', 'quantity',
        'unit')
    def on_change_unit(self, name=None):
        info_unit_price = self.on_change_with_info_unit_price()
        info_quantity = self.on_change_with_info_quantity()

        return {
            'info_unit_price': info_unit_price,
            'info_quantity': info_quantity,
            'info_quant': self.on_change_with_info_unit_price(),
            }

    @fields.depends('product', 'unit_price')
    def on_change_unit_price(self, name=None):
        if not self.product:
            return {}
        if self.unit_price:
            self.info_unit_price = self.product.get_info_unit_price(
                self.unit_price)
        else:
            self.info_unit_price = self.unit_price
        return {
            'info_unit_price': self.info_unit_price,
            }


class InvoiceLine(InformationUomMixin):
    __name__ = 'account.invoice.line'

    @classmethod
    def __setup__(cls):
        super(InvoiceLine, cls).__setup__()
        for value in cls.amount.on_change_with:
            if value not in cls.info_quantity.on_change:
                cls.info_quantity.on_change.add(value)
            if value not in cls.info_unit_price.on_change:
                cls.info_unit_price.on_change.add(value)
        if not 'invoice' in cls.currency_digits.on_change_with:
            cls.currency_digits.on_change_with.add('invoice')
        for value in ('invoice_type',):
            if value not in cls.info_unit_price.on_change:
                cls.info_unit_price.on_change.add(value)
                cls.info_unit_price.on_change_with.add(value)
                cls.info_unit_price.depends.append(value)

    @fields.depends('invoice')
    def on_change_with_currency_digits(self, name=None):
        if self.invoice:
            return self.invoice.currency_digits
        return 2
