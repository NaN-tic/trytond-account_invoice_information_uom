# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval, Bool, Not
from trytond.pool import Pool, PoolMeta
from decimal import Decimal

__all__ = ['Template']

_ZERO = Decimal('0.0')
_ROUND = Decimal('.0001')


class Template(metaclass=PoolMeta):
    __name__ = "product.template"
    use_info_unit = fields.Boolean('Use Information UOM')
    info_unit = fields.Many2One('product.uom', 'Information UOM',
        states={
            'required': Bool(Eval('use_info_unit'))
            })
    info_list_price = fields.Function(fields.Numeric('Information List Price',
            digits=(16, 8)),
        'on_change_with_info_list_price')
    info_ratio = fields.Float('Information Ratio', digits=(16, 4),
        states={
            'required': Bool(Eval('use_info_unit')),
            },
        domain=['OR',
            [('info_ratio', '=', None)],
            [('info_ratio', '!=', 0.0)],
                ])

    @classmethod
    def view_attributes(cls):
        return super(Template, cls).view_attributes() + [
            ('//page[@id="information_uom"]', 'states', {
                    'invisible': Not(Bool(Eval('use_info_unit'))),
                    })]

    def _compute_factor(self, factor=1.0, unit=None, base_unit=None):
        pool = Pool()
        Uom = pool.get('product.uom')
        if not base_unit:
            base_unit = self.default_uom
        if unit:
            factor = Uom.compute_qty(base_unit, factor, unit)
        return factor

    def calc_info_quantity(self, qty, unit=None):
        Uom = Pool().get('product.uom')
        if not self.use_info_unit or not qty:
            return 0.0
        if unit and unit != self.default_uom:
            qty = Uom.compute_qty(unit, qty, self.default_uom)
        return self.info_ratio * qty

    def calc_quantity(self, info_qty, unit=None):
        Uom = Pool().get('product.uom')
        if not info_qty or not self.use_info_unit:
            return 0.0
        info_qty = Uom.compute_qty(self.default_uom, float(info_qty), unit)
        return info_qty / self.info_ratio

    def get_info_list_price(self, unit=None):
        factor = self._compute_factor()
        price = _ZERO
        if self.use_info_unit and self.info_ratio and self.list_price:
            price = (self.list_price / Decimal(str(self.info_ratio))).quantize(
                _ROUND)
        return price / Decimal(str(factor))

    def get_unit_price(self, info_price, unit=None):
        price = _ZERO
        factor = self._compute_factor(1.0, unit)
        if self.use_info_unit:
            price = (info_price * Decimal(str(self.info_ratio))).quantize(
                _ROUND)
        return price / Decimal(str(factor))

    def get_info_unit_price(self, unit_price, unit=None):
        price = _ZERO
        factor = self._compute_factor(1.0, unit, self.info_unit)
        if self.use_info_unit:
            price = (unit_price / Decimal(str(self.info_ratio))).quantize(
                _ROUND)
        return (price * Decimal(str(factor))).quantize(_ROUND)

    @fields.depends('use_info_unit', 'info_price', 'info_ratio', 'default_uom',
        'list_price')
    def on_change_with_info_list_price(self, name=None):
        return self.get_info_list_price()
