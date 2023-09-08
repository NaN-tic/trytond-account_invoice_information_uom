# The COPYRIGHT file at the top level of this repository contains the full i
# copyright notices and license terms.
from trytond.pool import PoolMeta


class SaleLine(metaclass=PoolMeta):
    __name__ = 'sale.line'

    def get_invoice_line(self):
        invoice_line = super().get_invoice_line()
        if not invoice_line:
            return invoice_line
        invoice_line, = invoice_line
        invoice_line.on_change_unit()
        return [invoice_line]
