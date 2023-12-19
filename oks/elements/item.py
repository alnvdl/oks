from core.output import *
from core.db.row import Row
import oks


class Item(Row):
    TYPE = oks.ITEM

    def __init__(self, **kwargs):
        self.name = ""
        self.type_ = 0
        self.unit = 0
        self.quantity = 1
        self.price = 2.0
        self.notes = ""
        self.row = ("name", "type_", "unit", "quantity", "price", "notes")

        Row.__init__(self, **kwargs)

    def get_total_value(self):
        return self.quantity * self.price

    def make_output(self):
        item = Section("item_{0}".format(self.name), self.name)

        type_ = StringData("type", "Tipo", oks.ITEM_TYPES_DESC[self.type_])
        item.add_child(type_)

        unit = StringData("unit", "Unidade", oks.ITEM_UNITS_DESC[self.unit])
        item.add_child(unit)

        quantity = FloatData(
            "quantity", "Quantidade", self.quantity, strip_zeros=True
        )
        item.add_child(quantity)

        value = CurrencyData("value", "Valor", self.price, "R$")
        item.add_child(value)

        total = CurrencyData("total", "Total", self.get_total_value(), "R$")
        item.add_child(total)

        notes = StringData("notes", "Observações", self.notes)
        item.add_child(notes)

        return item
