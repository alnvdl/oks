from oks.gui.dialog import Dialog


class DialogExchangeItem(Dialog):
    def __init__(self, builder, parent):
        Dialog.__init__(
            self,
            builder,
            parent,
            "dialog_eitem",
            "entry_eitem_name",
            ("entry_eitem_name", "name"),
            ("spinbutton_eitem_quantity", "quantity"),
            ("entry_eitem_notes", "notes"),
        )
        self.set_size(380)

        completion = self.services["completion"]
        completion = completion("inventory:item")
        # Autocomplete the item's quantity
        completion.connect("match-selected", self.auto_set_quantity)
        self.entry_eitem_name.set_completion(completion)

    def auto_set_quantity(self, completion, table, rowIter):
        self.spinbutton_eitem_quantity.set_value(table.get_value(rowIter, 4))
