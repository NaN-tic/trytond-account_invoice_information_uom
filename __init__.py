# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import invoice
from . import sale


def register():
    Pool.register(
        invoice.InvoiceLine,
        module='account_invoice_information_uom', type_='model')
    Pool.register(
        sale.SaleLine,
        depends=['sale'],
        module='account_invoice_information_uom', type_='model')
