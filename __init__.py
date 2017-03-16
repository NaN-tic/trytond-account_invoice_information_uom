# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import template
from . import invoice


def register():
    Pool.register(
        template.Template,
        invoice.InvoiceLine,
        module='account_invoice_information_uom', type_='model')
