# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, If
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond import backend
from decimal import Decimal


class InvoiceLine:
    __name__ = 'account.invoce.line'

    info_unit = fields.Function(fields.Many2One('product.uom',
            'Information UOM',
            on_change_with=['product']), 'get_info_unit')
    info_unit_digits = fields.Function(fields.Integer(
        'Information Unit Digits', on_change_with=['info_unit']),
        'on_change_with_unit_digits')

    info_quantity = fields.Numeric('Information Quantity',
        digits=(16, Eval('unit_digits', 2)),
        states={
            'invisible': Eval('type') != 'line',
            'required': Eval('type') == 'line',
            },
        on_change_with=['quantity', 'product', 'info_quantity'],
        on_change=['quantity', 'unit_quantity', 'info_quantity']
        depends=['type', 'info_unit_digits'])

    info_unit_price = fields.Numeric('Information Unit Price', digits=(16, 4),
        states={
            'invisible': Eval('type') != 'line',
            'required': Eval('type') == 'line',
            },
        on_change=['unit_price', 'invoice_type']
        on_change_with=['unit_price', 'type', 'invoice_type',  'product'],
        depends=['type', 'invoice_type'])

    info_amount = fields.Function(fields.Numeric('Information Amount',
            digits=(16, Eval('_parent_invoice', {}).get('currency_digits',
                    Eval('currency_digits', 2))),
            states={
                'invisible': ~Eval('type').in_(['line', 'subtotal']),
                },
            on_change_with=['type', 'quantity', 'unit_price', 'info_quantity',
                '_parent_invoice.currency', 'currency'],
            depends=['type', 'currency_digits']), 'get_amount')

    def get_info_unit(self):
        if self.product and self.product.use_info_unit:
            return self.product.info_unit.id
        return None

    @staticmethod
    def default_info_unit_digits():
        return 2

    def on_change_with_unit_digits(self, name=None):
        if self.info_unit:
            return self.info_unit.digits
        return 2

    def on_change_with_info_unit(self, name=None):
        if not self.product or not self.product.use_info_unit:
            return None
        return self.product.info_unit.id

    def on_change_with_info_quantity(self, name=None):
        if not self.product:
            return
        return self.product.calc_info_quantity(self.qty)

    def on_change_info_quantity(self, name=None):
        if not self.product:
            return {}
        return {
            'qty': self.product.calc_info_quantity(self.info_qty, self.unit)
            }

    def on_change_with_info_unit_price(self, name=None):
        if not self.product:
            return
        return self.product.get_unit_price(self.info_unit_price)

    def on_change_info_unit_price(self, name=None):
        if not self.product:
            return {}
        return {
            'qty': self.product.calc_info_quantity(self.info_qty, self.unit)
            }

