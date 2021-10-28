# The COPYRIGHT file at the top level of this repository contains the full i
# copyright notices and license terms.

from trytond.model import fields
from trytond.pyson import Eval, Bool
from trytond.pool import PoolMeta, Pool
from decimal import Decimal
from trytond.modules.product import price_digits


__all__ = ['InformationUomMixin', 'InvoiceLine']

_ZERO = Decimal('0.0')
_ROUND = Decimal('.0001')

STATES = {
    'invisible': ~Bool(Eval('show_info_unit')),
    }
DEPENDS = ['show_info_unit']

class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    def get_invoice_line(self):
        invoice_line = super().get_invoice_line()
        if not invoice_line:
            return invoice_line
        invoice_line, = invoice_line
        invoice_line.on_change_unit()
        return [invoice_line]


class InformationUomMixin(object):
    __slots__ = ()
    show_info_unit = fields.Function(fields.Boolean('Show Information UOM'),
        'on_change_with_show_info_unit')
    info_unit = fields.Function(fields.Many2One('product.uom',
            'Information UOM', states=STATES, depends=DEPENDS),
        'on_change_with_info_unit')
    info_quantity = fields.Float('Information Quantity',
        digits='info_unit',
        states={
            'invisible': (~Bool(Eval('show_info_unit')) |
                (Eval('type') != 'line')),
            'required': (Bool(Eval('show_info_unit')) &
                (Eval('type') == 'line')),
            },
        depends=['type', 'show_info_unit'])
    info_unit_price = fields.Numeric('Information Unit Price',
        digits=price_digits,
        states={
            'invisible': (~Bool(Eval('show_info_unit')) |
                (Eval('type') != 'line')),
            'required': (Bool(Eval('show_info_unit')) &
                (Eval('type') == 'line')),
            },
        depends=['type', 'show_info_unit'])

    @classmethod
    def __setup__(cls):
        super(InformationUomMixin, cls).__setup__()
        for value in cls.amount.on_change_with:
            cls.info_quantity.on_change.add(value)
            cls.info_unit_price.on_change.add(value)
        for value in list(cls.amount.on_change_with) + ['product', 'quantity',
                'unit_price', 'unit']:
            cls.quantity.on_change.add(value)
            cls.unit.on_change.add(value)
            cls.unit_price.on_change.add(value)
        if hasattr(cls, 'gross_unit_price'):
            cls.info_unit_price.on_change_with.add('gross_unit_price')
            cls.quantity.depends.append('minimum_quantity')

    @fields.depends('product')
    def on_change_with_show_info_unit(self, name=None):
        if self.product and self.product.template.use_info_unit:
            return True
        return False

    @fields.depends('product')
    def on_change_with_info_unit(self, name=None):
        if (self.product and self.product.template.use_info_unit):
            return self.product.template.info_unit.id
        return None

    @fields.depends('product', 'quantity', 'unit')
    def on_change_with_info_quantity(self, name=None):
        if not self.product or not self.quantity:
            return
        return self.product.template.calc_info_quantity(self.quantity, self.unit)

    @fields.depends('product', 'info_quantity', 'unit',
        methods=['on_change_with_amount'])
    def on_change_info_quantity(self):
        if not self.product:
            return
        qty = self.product.template.calc_quantity(self.info_quantity, self.unit)
        self.quantity = qty
        self.amount = self.on_change_with_amount()

    @fields.depends('product', 'unit_price', 'type', 'product', 'info_unit', 'unit')
    def on_change_with_info_unit_price(self, name=None):
        Uom = Pool().get('product.uom')
        if not self.product or not self.unit_price or not self.unit:
            return
        price = self.unit_price
        if self.unit and self.unit != self.product.default_uom:
            price = Uom.compute_price(self.unit, price,
                self.product.default_uom)
        return self.product.template.get_info_unit_price(price, self.info_unit)

    @fields.depends('product', 'info_unit_price', 'unit',
        methods=['on_change_with_amount'])
    def on_change_info_unit_price(self):
        if not self.product or not self.info_unit_price:
            return

        self.unit_price = self.product.template.get_unit_price(
            self.info_unit_price, unit=self.unit)

        self.unit_price = self.unit_price
        if hasattr(self, 'gross_unit_price'):
            self.gross_unit_price = self.unit_price
            self.discount = Decimal('0.0')
        self.amount = self.on_change_with_amount()

    @fields.depends('product', 'quantity', 'unit')
    def on_change_quantity(self):
        if not self.product:
            return
        qty = self.product.template.calc_info_quantity(self.quantity, self.unit)
        self.info_quantity = float(qty)

    @fields.depends('product', 'unit_price', 'type', 'product', 'quantity',
        'unit')
    def on_change_unit(self):
        self.info_unit_price = self.on_change_with_info_unit_price()
        self.info_quantity = self.on_change_with_info_quantity()


    @fields.depends('product', 'unit_price', 'info_unit', 'unit')
    def on_change_unit_price(self):
        Uom = Pool().get('product.uom')

        if not self.product:
            return

        if self.unit_price:
            price = self.unit_price
            if self.unit and self.unit != self.product.default_uom:
                price = Uom.compute_price(self.unit, price,
                    self.product.template.default_uom)
            self.info_unit_price = self.product.template.get_info_unit_price(
                price, self.info_unit)
        else:
            self.info_unit_price = self.unit_price


class InvoiceLine(InformationUomMixin, metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @classmethod
    def __setup__(cls):
        super(InvoiceLine, cls).__setup__()
        for value in cls.amount.on_change_with:
            if value not in cls.info_quantity.on_change:
                cls.info_quantity.on_change.add(value)
            if value not in cls.info_unit_price.on_change:
                cls.info_unit_price.on_change.add(value)
        for value in ('invoice_type',):
            if value not in cls.info_unit_price.on_change:
                cls.info_unit_price.on_change.add(value)
                cls.info_unit_price.on_change_with.add(value)
                cls.info_unit_price.depends.append(value)
