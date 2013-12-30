# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime

from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Bool
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond import backend
from decimal import Decimal
import sys

__all__ = ['Template']
__metaclass__ = PoolMeta

_ZERO = Decimal('0.0')
_ROUND = Decimal('.0001')


class Template:
    __name__ = "product.template"

    use_info_unit = fields.Boolean('Use Information UOM')
    info_unit = fields.Many2One('product.uom', 'Information UOM',
        states={'required': Bool(Eval('use_info_unit'))})
    info_list_price = fields.Function(fields.Numeric('Information List Price',
            digits=(16, 8),
            on_change=['list_price', 'info_list_price',
                'info_ratio', 'use_info_unit'],
            on_change_with=['info_ratio', 'list_price', 'use_info_unit']),
        'on_change_with_info_list_price', setter='set_info_list_price')
    info_cost_price = fields.Function(fields.Numeric('Information Cost Price',
            digits=(16, 8), on_change=['cost_price', 'info_cost_price',
                'info_ratio', 'use_info_unit'],
            on_change_with=['info_ratio', 'cost_price', 'use_info_unit']),
        'on_change_with_info_cost_price', setter='set_info_cost_price')
    info_ratio = fields.Numeric('Information Ratio', digits=(16, 4),
            states={'required': Bool(Eval('use_info_unit'))})

    def calc_info_quantity(self, qty):
        if not self.use_info_unit:
            return _ZERO
        info_qty = self.info_ratio * Decimal(str(qty))
        print "a:", info_qty
        return info_qty

    def calc_quantity(self, info_qty, uom):
        if not self.use_info_unit:
            return _ZERO
        Uom = Pool().get('product.uom')
        qty = info_qty / self.info_ratio
        return (qty).quantize(_ROUND)

    def get_info_list_price(self):
        if self.use_info_unit and self.info_ratio and self.list_price:
            return (self.info_ratio * self.list_price).quantize(_ROUND)
        return _ZERO

    def get_info_cost_price(self, value=None):
        if not value:
            value = self.cost_price
        if self.use_info_unit and self.info_ratio and self.cost_price:
            return (self.info_ratio * value).quantize(_ROUND)
        return _ZERO

    def get_unit_price(self, info_price):
        if self.use_info_unit:
            return (info_price / self.info_ratio).quantize(_ROUND)
        return _ZERO

    def on_change_info_list_price(self, name=None):
        return {
            'list_price': self.get_unit_price(self.info_list_price)
            }

    def on_change_with_info_list_price(self, name=None):
        return self.get_info_list_price()

    def on_change_with_info_cost_price(self, name=None):
        return self.get_info_cost_price()

    def on_change_info_cost_price(self, name=None):
        return {
            'cost_price': self.get_unit_price(self.info_cost_price)
            }

    @classmethod
    def set_info_list_price(cls, templates, name, value):
        print >> sys.stderr, "hola:", templates, name, value
        
        if not value:
            return
        for template in templates:
            template.list_price = template.get_unit_price(value)
            template.save()

    @classmethod
    def set_info_cost_price(cls, templates, name, value):
        print >> sys.stderr, "hola2:", templates, name, value
        if not value:
            return
        for template in templates:
            template.cost_price = template.get_unit_price(value)
            template.save()
