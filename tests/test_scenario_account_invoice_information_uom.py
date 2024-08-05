import datetime
import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import \
    set_fiscalyear_invoice_sequences
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        today = datetime.date.today()

        # Activate module
        activate_modules('account_invoice_information_uom')

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create party
        Party = Model.get('party.party')
        party = Party(name='Party')
        party.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        kg, = ProductUom.find([('name', '=', 'Kilogram')])
        g, = ProductUom.find([('name', '=', 'Gram')])
        ProductTemplate = Model.get('product.template')
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.use_info_unit = True
        template.info_unit = kg
        template.info_ratio = Decimal('2')
        template.type = 'service'
        template.list_price = Decimal('40')
        template.account_category = account_category
        template.save()
        self.assertEqual(template.info_list_price, Decimal('20.0000'))
        product, = template.products
        product.save()

        # Create payment term
        PaymentTerm = Model.get('account.invoice.payment_term')
        PaymentTermLine = Model.get('account.invoice.payment_term.line')
        payment_term = PaymentTerm(name='Term')
        payment_term_line = PaymentTermLine(type='remainder')
        payment_term.lines.append(payment_term_line)
        payment_term.save()

        # Create invoice
        Invoice = Model.get('account.invoice')
        InvoiceLine = Model.get('account.invoice.line')
        invoice = Invoice()
        invoice.type = 'out_invoice'
        invoice.party = party
        invoice.payment_term = payment_term
        invoice.invoice_date = today
        line = InvoiceLine()
        invoice.lines.append(line)
        line.product = product
        self.assertEqual(line.show_info_unit, True)
        line.unit_price = Decimal('40')
        self.assertEqual(line.info_unit_price, Decimal('20.0000'))
        self.assertEqual(line.unit, unit)
        self.assertEqual(line.info_unit, kg)
        line.quantity = 5
        self.assertEqual(line.info_quantity, 10.0)
        self.assertEqual(line.amount, Decimal('200.00'))
        line.unit_price = Decimal('50')
        self.assertEqual(line.info_unit_price, Decimal('25.0000'))
        self.assertEqual(line.amount, Decimal('250.00'))
        line.info_unit_price = Decimal('20')
        self.assertEqual(line.unit_price, Decimal('40'))
        self.assertEqual(line.amount, Decimal('200.00'))
        line.info_unit = g
        self.assertEqual(line.info_unit_price, Decimal('20000.0000'))
        self.assertEqual(line.unit_price, Decimal('40'))
        self.assertEqual(line.amount, Decimal('200.00'))

        # Supplier invoice
        Invoice = Model.get('account.invoice')
        InvoiceLine = Model.get('account.invoice.line')
        invoice = Invoice()
        invoice.type = 'in_invoice'
        invoice.party = party
        invoice.payment_term = payment_term
        invoice.invoice_date = today
        line = InvoiceLine()
        invoice.lines.append(line)
        line.product = product
        self.assertEqual(line.show_info_unit, True)
        line.unit_price = Decimal('20.0000')
        self.assertEqual(line.info_unit_price, Decimal('10.0000'))
        self.assertEqual(line.unit, unit)
        self.assertEqual(line.info_unit, kg)
        line.quantity = 5
        self.assertEqual(line.info_quantity, 10.0)
        self.assertEqual(line.amount, Decimal('100.00'))
        line.unit_price = Decimal('50')
        self.assertEqual(line.info_unit_price, Decimal('25.0000'))
        self.assertEqual(line.amount, Decimal('250.00'))
        line.info_unit_price = Decimal('20')
        self.assertEqual(line.unit_price, Decimal('40'))
        self.assertEqual(line.amount, Decimal('200.00'))
        line.info_unit = g
        self.assertEqual(line.info_unit_price, Decimal('20000.0000'))
        self.assertEqual(line.unit_price, Decimal('40'))
        self.assertEqual(line.amount, Decimal('200.00'))
