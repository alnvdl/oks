#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime

from core.db.models.internal import FilteredInternalModel
from oks.gui.dialog import Dialog
from oks.elements.company import Company
from oks.elements.item import Item
from oks.elements.operation import Operation
from oks.elements.operation.product import Product
from oks.elements.operation.pitem import ProductionItem
from oks.elements.operation.pitem.rawmaterial import RawMaterial
from oks.elements.operation.eitem import ExchangeItem
from oks.elements.operation.transaction import Transaction
from oks.gui.dialogs.product import DialogProduct
from oks.gui.dialogs.eitem import DialogExchangeItem
from oks.gui.dialogs.pitem import DialogProductionItem
from oks.gui.dialogs.transaction import DialogTransaction
from oks.gui.columns import *
from oks.gui.entrydate import EntryDate
import oks

DIALOGS = {
    oks.PRODUCT: DialogProduct,
    oks.PRODUCTION_ITEM: DialogProductionItem,
    oks.EXCHANGE_ITEM: DialogExchangeItem,
    oks.TRANSACTION: DialogTransaction,
}

TYPE_TO_ELEMENT = {
    oks.PRODUCT: Product,
    oks.PRODUCTION_ITEM: ProductionItem,
    oks.EXCHANGE_ITEM: ExchangeItem,
    oks.TRANSACTION: Transaction,
}


class DialogOperation(Dialog):
    def __init__(self, builder, parent):
        Dialog.__init__(
            self,
            builder,
            parent,
            "dialog_operation",
            "entry_operation_company",
            ("entry_operation_company", "company"),
            ("spinbutton_operation_oid", "oid"),
            ("entry_operation_notes", "notes"),
        )
        self.load_widget("hbox_operation_date")
        self.load_widget("label_top")
        self.load_widget("label_bottom")
        self.load_widget("vbox_top")
        self.load_widget("vbox_bottom")
        self.load_widget("treeview_top")
        self.load_widget("treeview_bottom")

        self.get_selected_top = (
            lambda *args: self.treeview_top.get_selection().get_selected()[1]
        )
        self.get_selected_bottom = (
            lambda *args: self.treeview_bottom.get_selection().get_selected()[
                1
            ]
        )

        # Load the buttons
        for button in (
            "button_top_add",
            "button_top_edit",
            "button_top_remove",
            "button_bottom_add",
            "button_bottom_edit",
            "button_bottom_remove",
        ):
            widget = self.get_widget(button)
            widget.connect(
                "clicked", self.on_button_clicked, button.split("_")[1:]
            )
            setattr(self, button, widget)

        # Setting the company completion
        completion = self.services["completion"]
        self.entry_operation_company.set_completion(
            completion("companies:name")
        )

        # Setting the date widget...
        self.entry_date = EntryDate(self, "date")
        self.register_field("entry_date", self.entry_date)
        self.hbox_operation_date.pack_start(self.entry_date.widget)
        self.hbox_operation_date.show_all()

    def load_from_content(self, content):
        self.content = content

        # Setting the operation type as the title
        self.set_title(
            "Operação de %s" % oks.OPERATION_TYPES_DESC[content.type_]
        )

        # Deciding which type of list to use...
        itemsList = {
            "model_cols": [
                ("name", str),
            ],
            "columns": [
                (TextColumn, "Item", 0),
            ],
        }

        transactionsList = {
            "model_cols": [("ddate", str), ("value", float)],
            "columns": [
                (DateColumn, "Data", 0),
                (CurrencyColumn, "Valor (R$)", 1),
            ],
        }

        # Setting views
        for io in ("top", "bottom"):
            type_ = None
            io_flag = getattr(content, io)
            if io_flag == oks.INPUT:
                type_ = content.inputType[0]
            elif io_flag == oks.OUTPUT:
                type_ = content.outputType[0]

            list_ = None
            if type_ in (oks.PRODUCT, oks.PRODUCTION_ITEM, oks.EXCHANGE_ITEM):
                list_ = itemsList
            elif type_ in (oks.TRANSACTION, oks.EXCHANGE_ITEM):
                list_ = transactionsList

            vbox = getattr(self, "vbox_{0}".format(io))
            label = getattr(self, "label_{0}".format(io))
            label.set_text(
                "<b>%s</b>" % getattr(content, "{0}Name".format(io))
            )
            label.set_use_markup(True)

            if list_:
                vbox.set_visible(True)
                label.set_visible(True)

                model = content.output
                if getattr(content, io) == oks.INPUT:
                    model = content.input

                fmodel = FilteredInternalModel(model, *list_["model_cols"])
                setattr(self, "model_{0}".format(io), fmodel)
                treeview = getattr(self, "treeview_{0}".format(io))
                treeview.set_model(fmodel.filteredModel)

                for column in treeview.get_columns():
                    treeview.remove_column(column)

                for column in list_["columns"]:
                    col_class, col_label, col_index = column
                    column = col_class(col_label, col_index)
                    treeview.append_column(column)
            else:
                vbox.set_visible(False)
                label.set_visible(False)

        # Resize the window to its minimal size, because it can change
        # self.window.resize(1, 1)
        Dialog.load_from_content(self, content)

    def get_element(self, IO):
        if IO == 0:
            return TYPE_TO_ELEMENT[self.content.outputType[0]]()
        elif IO == 1:
            return TYPE_TO_ELEMENT[self.content.inputType[0]]()

    # Actions
    def on_button_clicked(self, widget, data):
        pos, action = data

        if pos == "top":
            model = self.model_top
            if action == "add":
                a = self.content.top
                b = self.content.bottom
            elif action == "edit" or action == "remove":
                iter_ = self.get_selected_top()
        elif pos == "bottom":
            model = self.model_bottom
            if action == "add":
                a = self.content.bottom
                b = self.content.top
            elif action == "edit" or action == "remove":
                iter_ = self.get_selected_bottom()

        if action == "add":
            element = self.get_element(a)
            # Set the value for the operation based on the items
            if element.TYPE == oks.TRANSACTION:
                element.value = self.content.get_total_value(
                    b
                ) - self.content.get_total_value(a)
                settings = self.services["settings"]
                element.ddate = datetime.date.today() + datetime.timedelta(
                    settings("DEFAULT_TRANSACTION_DEADLINE")
                )
            self.run_editor(DIALOGS[element.TYPE], model.insert, element)
        elif action == "edit" and iter_:
            element = model.get_object(iter_)
            self.run_editor(
                DIALOGS[element.TYPE], model.update, element, iter_
            )
        elif action == "remove" and iter_:
            model.delete(iter_)
