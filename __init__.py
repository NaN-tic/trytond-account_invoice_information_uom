#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
from template import *

def register():
    Pool.register(
        Template,
        module='account_invoice_information_uom', type_='model')
