# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.model import fields
from trytond.pyson import Eval, If
from trytond.pool import PoolMeta
from decimal import Decimal

__all__ = ['InvoiceLine']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')
_ROUND = Decimal('.0001')


class InvoiceLine:
    __name__ = 'account.invoice.line'

    info_unit = fields.Function(fields.Many2One('product.uom',
            'Information UOM',
            on_change_with=['product']), 'on_change_with_info_unit')
    info_unit_digits = fields.Function(fields.Integer(
        'Information Unit Digits', on_change_with=['info_unit']),
        'on_change_with_unit_digits')

    info_quantity = fields.Numeric('Information Quantity',
        digits=(16, Eval('unit_digits', 2)),
        states={
            'invisible': Eval('type') != 'line',
            'required': Eval('type') == 'line',
            },
        on_change_with=['quantity', 'product', 'info_quantity',
            'info_unit_price', 'product'],
        on_change=['quantity', 'unit_quantity', 'unit',
            'info_quantity', 'info_unit_price', 'product'],
        depends=['type', 'info_unit_digits', 'product', 'unit', 'unit_digits'])

    info_unit_price = fields.Numeric('Information Unit Price', digits=(16, 4),
        states={
            'invisible': Eval('type') != 'line',
            'required': Eval('type') == 'line',
            },
        on_change=['info_unit_price', 'invoice_type', 'product', 'info_quantity',
            'invoice_type', 'type'],
        on_change_with=['unit_price', 'type', 'invoice_type',
            'info_unit_price', 'info_quantity', 'product', 'unit_price'],
        depends=['type', 'invoice_type', 'product'])

    info_amount = fields.Function(fields.Numeric('Information Amount',
            digits=(16, Eval('_parent_invoice', {}).get('currency_digits',
                    Eval('currency_digits', 2))),
            states={
                'invisible': ~Eval('type').in_(['line', 'subtotal']),
                },
            on_change_with=['type', 'info_unit_price',
                'info_quantity', '_parent_invoice.currency', 'currency'],
            depends=['type', 'currency_digits']), 'get_amount')

    @staticmethod
    def default_info_unit_digits():
        return 2

    def on_change_with_unit_digits(self, name=None):
        if self.info_unit:
            return self.info_unit.digits
        return 2

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
        return {
            'quantity': float(qty)
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
        return {
            'unit_price': self.product.get_unit_price(self.info_unit_price)
            }

    def on_change_with_info_amount(self, name=None):
        return self.info_unit_price * self.info_quantity
