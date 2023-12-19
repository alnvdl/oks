from oks.gui.dialog import Dialog
import oks


class DialogItem(Dialog):
    def __init__(self, builder, parent):
        Dialog.__init__(
            self,
            builder,
            parent,
            "dialog_item",
            "entry_item_name",
            ("entry_item_name", "name"),
            ("combobox_item_type", "type_"),
            ("combobox_item_unit", "unit"),
            ("spinbutton_item_quantity", "quantity"),
            ("spinbutton_item_price", "price"),
            ("entry_item_notes", "notes"),
        )
        self.set_size(380)
        self.combobox_item_type.set_options(*oks.ITEM_TYPES_DESC[:-1])
        self.combobox_item_unit.set_options(*oks.ITEM_UNITS_DESC[:-1])
