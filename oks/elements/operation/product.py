from core.output import *
from oks.elements.operation import OperationElement
import oks


class Product(OperationElement):
    TYPE = oks.PRODUCT

    def __init__(self, **kwargs):
        self.name = ""
        self.quantity = 1
        self.price = 2.0
        self.notes = ""
        self.row = ("name", "quantity", "price", "notes")

        OperationElement.__init__(self, **kwargs)

    def get_value_for_operation(self):
        return self.quantity * self.price

    def make_output(self):
        product = Section("product_{0}".format(self.row_id), self.name)

        quantity = FloatData(
            "quantity", "Quantidade", self.quantity, strip_zeros=True
        )
        product.add_child(quantity)

        price = CurrencyData("value", "Valor", self.price, "R$")
        product.add_child(price)

        total = CurrencyData(
            "total", "Total", self.get_value_for_operation(), "R$"
        )
        product.add_child(total)

        notes = StringData("notes", "Observações", self.notes)
        product.add_child(notes)

        return product
