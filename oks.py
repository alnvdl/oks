#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys
import os.path
import datetime
import re
import locale

import gtk
import gobject

from core.output.handlers.string import StringOutputHandler
from core.output.handlers.view import ViewOutputHandler
import oks
from oks.db.manager import DatabaseManager
from oks.db.app import (TABLE_COMPANIES, TABLE_INVENTORY, TABLE_OPERATIONS, 
                        TABLE_TRANSACTIONS_VIEW, TABLE_TO_TYPE)
from oks.elements.company import Company
from oks.elements.item import Item
from oks.elements.operation import Operation
from oks.elements.operation.product import Product
from oks.elements.operation.pitem import ProductionItem
from oks.elements.operation.pitem.rawmaterial import RawMaterial
from oks.elements.operation.eitem import ExchangeItem
from oks.elements.operation.transaction import Transaction
from oks.reports import companies, inventory, operations, transactions
from oks.gui.window import Window
from oks.gui.dialogs.company import DialogCompany
from oks.gui.dialogs.operation import DialogOperation
from oks.gui.dialogs.item import DialogItem
from oks.gui.dialogs.operation_type import DialogSelectOperationType
from oks.gui.entrydate import EntryDate
from oks.gui.fields import *
from oks.gui.columns import *
from oks.gui.title import Title
from oks.gui.printaction import PrintAction
from oks.gui.searchbox import SearchBox

def clear_gtk_container(container):
    for child in container.get_children():
        container.remove(child)
        
        
class DialogTable(Window):        
    AUTO_UPDATE_SEARCH = True
    SORT = True
    
    def __init__(self, gladeFile, db_path):
        # Initiating the dialog
        builder = gtk.Builder()
        builder.add_from_file(gladeFile)
        Window.__init__(self, builder, "main")
        self.set_size(1300, 800) # Makes the hpaned be place appropriately
        self.window.maximize()
                    
        # Loading some required widgets
        self.load_widget("hpaned")
        self.load_widget("treeview")
        self.load_widget("vbox_main")
        self.load_widget("toolbar")
        self.load_widget("toolbar_separator")
        self.load_widget("toolbutton_add")
        self.load_widget("toolbutton_switch_mode")
        self.load_widget("vbox_right")
        self.load_widget("vbox_left_main")
        self.load_widget("action_view_reports")
        self.load_widget("action_view_main")
        self.load_widget("vbox_left_reports")
        self.load_widget("action_new")
        self.load_widget("dialogAbout")
        self.load_widget("combobox_report_type")
        self.load_widget("label_report_description")
        self.load_widget("table_report_options")
        self.load_widget("vbox_report_options_frame")
        self.load_widget("statusbar")
        self.load_widget("label_report_options")
                
        self.current_left = None
        
        # Setting the view area
        self.title = Title(self.window, "Açõe_s")
        self.title.enable_actions(False)
        
        self.vbox_right.pack_start(self.title, False, False)
        self.vbox_right.reorder_child(self.title, 0)
        
        self.hpaned.pack2(self.vbox_right, True, False)

        # Report selection area
        attributes = pango.AttrList()
        attributes.insert(pango.AttrStyle(pango.STYLE_ITALIC, 0, -1))
        self.label_report_description.set_attributes(attributes)
        self.combobox_report_type = ComboBoxField(self.combobox_report_type, 
                                                  None,
                                                  gobject.TYPE_STRING,
                                                  gobject.TYPE_PYOBJECT) 
        self.combobox_report_type.connect("new-value",
                                          self.on_report_type_selected)

        # Setting the view area
        self.textview = TextViewField(self.get_widget("textview"))
        self.textview.widget.set_editable(False)
        self.textview.set_font("monospace")      
        
        # Search
        self.search_timeout = 0
        self.search_box = SearchBox(self.AUTO_UPDATE_SEARCH)
        self.search_box.connect("search-updated", self.auto_update_search)
        self.get_widget("vbox_search").pack_start(self.search_box, False)
        
        # statusbar
        self.statusbar.get_context_id("oks")
                
        # Tables and Reports
        self.tables = {}
        self.reports = {}
        # Defining the default tables. Each table has a set of properties
        # that are keys in a dictionary:
        #
        # window_title: the window title
        # columns: the TreeViewColumns used by the table
        # default_sort: the default sort column and order
        # search_widgets: the fields that will be put in the SearchBox
        # editable: True if the table can be edited (add, remove, edit)
        # new_stock: the stock for the new element that a table can hold
        # completion: the completion for the search_widgets
        
        #
        # Companies 
        #
        entryName = EntryField(gtk.Entry(), "name")
        entryCity = EntryField(gtk.Entry(), "city")
        
        self.tables[TABLE_COMPANIES] = {
        "window_title": "Empresas",
        
        "columns": [        
        TextColumn("Nome", 1, self.SORT, True),
        TypeColumn("Tipo", 2, oks.COMPANY_TYPES_DESC, self.SORT),
        TextColumn("Telefone", 9, self.SORT, True)],
        
        "default_sort": (1, gtk.SORT_ASCENDING),
        
        "search_widgets": [
        ("Nome: ", entryName),
        ("Cidade: ", entryCity)],
        
        "actions": [
        ("_Editar", self.edit),
        ("_Remover", self.remove),
        ("_Imprimir", self.print_action),
        ("Imprimir e_tiqueta de correio", self.print_label)],
        
        "new_stock": "Nova empresa",
        
        "completion": [(entryCity, "companies:city")],
        
        "reports": [companies.FullCompaniesReport,
                    companies.CompactCompaniesReport,
                    companies.MostImportantCompanies],
        
        "main_state": (None, None),

        "report_state": (None, None),
        }
        
        #
        # Inventory
        #
        combobox_type = ComboBoxField(gtk.ComboBox(), "type_")
        combobox_type.set_options(*oks.ITEM_TYPES_DESC)
        combobox_type.set_defaultValue(oks.TYPE_ITEMS_ALL)
        combobox_type.clear()
        
        entry_item = EntryField(gtk.Entry(), "name")
        
        self.tables[TABLE_INVENTORY] = {
        "window_title": "Inventário",
        
        "columns": [        
        TextColumn("Item", 1, self.SORT, True),
        TypeColumn("Tipo", 2, oks.ITEM_TYPES_DESC, self.SORT),
        FloatColumn("Quantidade", 4, self.SORT),
        CurrencyColumn("Valor (R$)", 5, self.SORT)],
        
        "default_sort": (1, gtk.SORT_ASCENDING),

        "search_widgets": [ ("Item: ", entry_item),
                            ("Tipo: ", combobox_type) ],
        
        "actions": [("_Editar", self.edit), 
                    ("_Remover", self.remove)],
        
        "new_stock": "Novo item",
        
        "reports": [inventory.InventoryReport,
                    inventory.MostImportantItems],
        
        "main_state": (None, None),

        "report_state": (None, None),  
        }
                
        #
        # Operations
        #
        column_status = CheckButtonColumn("Status", 6)
        column_status.cellRenderer.connect("toggled", 
                                           self.on_operation_status_change)

        combobox_type = ComboBoxField(gtk.ComboBox(), "type_")
        combobox_type.set_options(*oks.OPERATION_TYPES_DESC)
        combobox_type.set_defaultValue(oks.TYPE_OPERATIONS_ALL)
        combobox_type.clear()
        
        entryCompany = EntryField(gtk.Entry(), "company")
        entry_item = EntryField(gtk.Entry(), "name")
        entry_date = EntryDate(self, "date", True)
        entry_date.set_value(None)
        
        self.tables[TABLE_OPERATIONS] = {
        "window_title": "Operações",
        
        "columns": [
        DateColumn("Data", 4, self.SORT),
        TypeColumn("Tipo", 1, oks.OPERATION_TYPES_DESC, self.SORT),
        TextColumn("Empresa", 2, self.SORT, ellipsize = True),
        IntegerColumn("ID", 3, self.SORT),
        column_status],
        
        "default_sort": (4, gtk.SORT_DESCENDING),
        
        "search_widgets": [ ("Empresa: ", entryCompany),
                            ("Item: ", entry_item),
                            ("Período: ", entry_date), 
                            ("Tipo: ", combobox_type) ],
        
        "actions": [
        ("_Editar", self.edit),
        ("_Remover", self.remove),
        ("_Imprimir", self.print_action),
        ("Dar _acabamento", self.finishing),
        ("_Copiar operação", self.copy_operation),
        ("Re_solver requisitos", self.resolve_reqs)],
        
        "new_stock": "Nova operação",
        
        "completion": [(entryCompany, "companies:name"),
                       (entry_item, "inventory:item")],
        
        "reports": [operations.OutgoingOperationsReport,
                    operations.IncomingOperationsReport,
                    operations.ProductionOperationsReport,
                    operations.ProductionCostReport,
                    operations.ProductionSalesReport],

        "main_state": (None, None),

        "report_state": (None, None),
        }

        
        #
        # Transactions
        #
        column_status = CheckButtonColumn("Status", 7)
        column_status.cellRenderer.connect("toggled",
                                          self.on_transactionStatusChanged)
        
        entryCompany = EntryField(gtk.Entry(), "company")            
        
        combobox_type = ComboBoxField(gtk.ComboBox(), "type_")
        combobox_type.set_options(*oks.TRANSACTION_TYPES_DESC)
        combobox_type.set_defaultValue(oks.TYPE_TRANSACTIONS_ALL)
        combobox_type.clear()
        
        comboboxStatus = ComboBoxField(gtk.ComboBox(), "status")
        comboboxStatus.set_options(*oks.TRANSACTION_STATUS_DESC)
        comboboxStatus.set_defaultValue(oks.TYPE_STATUS_ALL)
        comboboxStatus.clear()
        
        entry_date = EntryDate(self, "date", True)
        entry_date.set_value(None)
        
        self.tables[TABLE_TRANSACTIONS_VIEW] = {
        "window_title": "Transações",
        
        "columns": [DateColumn("Data", 2, self.SORT),
                    TypeColumn("Tipo", 1, oks.TRANSACTION_TYPES_DESC,
                               self.SORT, True),
                    TextColumn("Empresa", 3, self.SORT, True),
                    IntegerColumn("ID", 4, self.SORT),
                    CurrencyColumn("Valor (R$)", 6, self.SORT),
                    column_status],
            
        "default_sort": (2, gtk.SORT_DESCENDING),
        
        "search_widgets": [ ("Empresa: ", entryCompany),
                            ("Período: ", entry_date),
                            ("Status: ", comboboxStatus),
                            ("Tipo: ", combobox_type) ],
        
        "actions": [],
        
        "new_stock": None,
        
        "completion": [(entryCompany, "companies:name")],
        
        "reports":  [transactions.PayablesReport,
                     transactions.ReceivablesReport],

        "main_state": (None, None),

        "report_state": (None, None),
        }
   
        # Load the database
        self.db_man = DatabaseManager(db_path)
        self.db_man.open_db()
        self.load_db(self.db_man.db)
        
    #              
    # Database management
    #
    def load_db(self, db):
        self.models = {}
        self.reports = {}
        self.table = None
        self.selected = None
        self.mode = None
        self.db = db
        self.services = self.db.services
        # Load the main mode
        self.set_mode(oks.MODE_MAIN)
        
    def on_action_import_db_activate(self, action):
        response = self.show_message("Importar base de dados?", 
                                     "Importar uma base de dados vai "\
                                     "sobrescrever a base de dados atual. "\
                                     "Deseja prosseguir?",
                                     gtk.MESSAGE_QUESTION,
                                     gtk.BUTTONS_YES_NO)
        if response != gtk.RESPONSE_YES:
            return
        
        dialog = gtk.FileChooserDialog("Importar")
        file_filter = gtk.FileFilter()
        file_filter.set_name("SQLite3 database")
        file_filter.add_mime_type("application/x-sqlite3")   
        dialog.add_filter(file_filter)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dialog.add_button(gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        dialog.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.db_man.import_db(dialog.get_filename())
            self.load_db(self.db_man.db)
        dialog.hide()
        dialog.destroy()
        
    def on_action_export_db_activate(self, action):
        dialog = gtk.FileChooserDialog("Exportar")
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dialog.add_button(gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        dialog.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name("db-%s" % str(datetime.date.today()))
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.db_man.export_db(dialog.get_filename())
            self.load_db(self.db_man.db)
        dialog.hide()
        dialog.destroy()

    #
    # Mode setting
    #        
    def set_mode(self, mode):
        self.save_state()
        if mode == oks.MODE_MAIN:
            self.toolbar.remove(self.toolbar_separator)
            self.toolbar.insert(self.toolbar_separator, 5)
            self.toolbutton_add.show()
            self.action_view_reports.connect_proxy(self.toolbutton_switch_mode)
            left = self.vbox_left_main
        elif mode == oks.MODE_REPORT:
            self.toolbar.remove(self.toolbar_separator)
            self.toolbar.insert(self.toolbar_separator, 4)
            self.toolbutton_add.hide()
            self.action_view_main.connect_proxy(self.toolbutton_switch_mode)
            left = self.vbox_left_reports
        
        if self.current_left is not None:
            self.hpaned.remove(self.current_left)
        self.hpaned.pack1(left, True, False)
        self.current_left = left
        
        for child in self.toolbar.get_children():
            child.set_is_important(True)
                    
        self.mode = mode
        self.get_widget("radioaction_show_operations").toggled()        

        self.load_table(TABLE_OPERATIONS, True)
        self.get_widget("radioaction_show_operations").activate()
        
        self.set_statusbar_message()
        
    def on_action_mode_activate(self, action):
        if self.mode == oks.MODE_MAIN:
            self.set_mode(oks.MODE_REPORT)
        else:
            self.set_mode(oks.MODE_MAIN)
            
    #     
    # Tables
    #
    def save_state(self):
        if self.mode == oks.MODE_MAIN:
            model, iter_ = self.treeview.get_selection().get_selected()
            path = None
            if iter_ is not None:
                path = model.get_path(iter_)
            scroll = self.treeview.get_visible_rect()
            self.tables[self.table]["main_state"] = (path, scroll)
        elif self.mode == oks.MODE_REPORT:
            report = self.combobox_report_type.get_value()
            self.tables[self.table]["report_state"] = (report, None)
                        
    def load_table(self, table, force_reload=False):
        if table == self.table and not force_reload:
            return
        if self.tables.has_key(table):
            if table != self.table and self.table:
                # Save the current state
                self.save_state()
                self.clear_view()
            self.table = table
        else:
            raise KeyError, "The table %s is not supported." % table
        
        # If we are in report mode, just set it and ignore the table setting
        if self.mode == oks.MODE_REPORT:
            # Clear the previous report description and options
            self.label_report_description.set_text("")
            clear_gtk_container(self.table_report_options)
        
            self.window.set_title("Relatórios")
            self.vbox_report_options_frame.hide_all()
            
            reports = self.tables[table]["reports"]
            reports = [(report.NAME, report) for report in reports]
            self.combobox_report_type.set_options(*reports)
            
            # Restore the previous state
            report, scroll = self.tables[self.table]["report_state"]
            if report is not None:
                self.combobox_report_type.set_value(report)
                
            self.hpaned.set_position(300)
            return
            
        # Window title
        self.window.set_title(self.tables[table]["window_title"])
        
        # Search
        self.search_box.reset()
        for (label, searchWidget) in self.tables[table]["search_widgets"]:
            self.search_box.add_field(label, searchWidget)
        
        # Actions
        self.title.enable_actions(False)
        self.actions_enabled = not self.tables[table]["actions"] == []
        self.title.set_actions(*self.tables[table]["actions"])
        
        # Treeview
        if table not in self.models.keys():
            self.model = self.db.models[table]
            self.f_model = self.model.filter_new()
            self.f_model.set_visible_func(self.visible_func)
            self.sf_model = None
            if self.SORT:      
                self.sf_model = gtk.TreeModelSort(self.f_model)
                sort_col, sort_type = self.tables[table]["default_sort"]
                if sort_col is not None and sort_type is not None:
                    self.sf_model.set_sort_column_id(sort_col, sort_type)
            self.models[table] = (self.model, self.f_model, self.sf_model)
        else:
            self.model, self.f_model, self.sf_model = self.models[table]
                
        for column in self.treeview.get_columns():
            self.treeview.remove_column(column)
        for column in self.tables[table]["columns"]:
            self.treeview.append_column(column)
        self.selected = None
                
        self.reload_search(False)
        if self.SORT:
            model = self.sf_model
        else:
            model = self.f_model
        self.treeview.set_model(model)

        action_new_label = self.tables[table]["new_stock"]
        if action_new_label:
            self.action_new.set_sensitive(True)
            self.action_new.set_property("label", action_new_label)
            self.action_new.set_property("short_label", action_new_label)
        else:
            self.action_new.set_sensitive(False)
        
        # Completion support
        completion = self.services["completion"]
        if self.tables[table].has_key("completion"):
            for entry, completion_name in self.tables[table]["completion"]:
                entry.set_completion(completion(completion_name))
        
                
        # Restore the previous state
        element, scroll = self.tables[self.table]["main_state"]
        if element is not None:
            self.treeview.get_selection().select_path(element)
            self.on_treeview_cursor_changed()
        else:
            self.clear_view()
        
        if scroll is not None:
            # Add a timeout to prevent flickering
            cb = lambda: self.treeview.scroll_to_point(scroll.x, scroll.y);\
                         False
            gobject.timeout_add(250, cb)
        
        self.hpaned.set_position(420)
        self.search_box.grab_focus()
        self.f_model.refilter() # Refilter, so that the sorting works fine
    
    def on_radioaction_show_changed(self, widget, current):
        tables = [TABLE_COMPANIES,
                  TABLE_INVENTORY,
                  TABLE_OPERATIONS,
                  TABLE_TRANSACTIONS_VIEW]

        table = tables[current.get_current_value()]
        self.load_table(table)

    def reload_search(self, refilter=True):
        query_functions = {
        TABLE_COMPANIES: self.db.query_companies,
        TABLE_INVENTORY: self.db.query_inventory,
        TABLE_OPERATIONS: self.db.query_operations,
        TABLE_TRANSACTIONS_VIEW: self.db.query_transactions}

        results = query_functions[self.table](self.search_box.get_search())
        results = tuple([row_id for (row_id,) in results])
        
        self.results = {}
        for row in self.model:
            row_id = self.model.get_value(row.iter, 0)
            self.results[row_id] = row_id in results
        
        if refilter:
            self.f_model.refilter()
        
        if self.treeview.get_selection().get_selected()[1] is None:
            self.clear_view()

        # Scroll to the top when search is done
        model = self.treeview.get_model()
        if model is not None:
            first = model.get_iter_first()
            if first is not None:
                model.get_path(first)
                self.treeview.scroll_to_cell(model.get_path(first))

    # The function used for filtering the model based on the query results
    def visible_func(self, model, iter_):
        return self.results.get(model.get_value(iter_, 0))
        
    # Sets a timeout used when auto updating       
    def auto_update_search(self, *args):
        if self.search_timeout != 0:
            gobject.source_remove(self.search_timeout)
        self.search_timeout = gobject.timeout_add(500, self.reload_search)
    
    #
    # Element selection
    #    
    def get_selected_row_id(self):
        rowIter = self.treeview.get_selection().get_selected()[1]
        if self.SORT:
            rowIter = self.sf_model.convert_iter_to_child_iter(None, rowIter)
        rowIter = self.f_model.convert_iter_to_child_iter(rowIter) 
        return self.model.get_row_id(rowIter)
        
    def get_row_id_from_path(self, path):
        if self.SORT:
            path = self.sf_model.convert_path_to_child_path(path)
        path = self.f_model.convert_path_to_child_path(path)
        rowIter = self.model.get_iter(path)
        return self.model.get_row_id(rowIter)
    
    def assert_selected(self):
        if self.selected:
            return True
        else:
            self.show_message("Nenhum elemento selecionado", 
                              "É preciso selecionar um elemento da tabela"\
                              "para efetuar esta ação.")
            return False
        
    # Load an element when it is selected
    def on_treeview_cursor_changed(self, widget = None):
        row_id = self.get_selected_row_id()
        element = self.db.load(TABLE_TO_TYPE[self.table], row_id = row_id)
        self.selected = element
        voh = ViewOutputHandler()
        title, content = voh.output(element.make_output())
        self.title.set_label(title)
        self.textview.set_value(content)
        if self.actions_enabled:
            self.title.enable_actions(True)
            
    # Create a new element when the toolbutton new is clicked
    def on_action_new_activate(self, widget):
        if self.table == TABLE_COMPANIES:
            response = self.run_editor(DialogCompany, self.db.save, Company())
        elif self.table == TABLE_INVENTORY:
            response = self.run_editor(DialogItem, self.db.save, Item())
        elif self.table == TABLE_OPERATIONS:
            dialog = DialogSelectOperationType(self.builder, self)
            response, type_, negative = dialog.run()
            dialog.close()
            if response == gtk.RESPONSE_OK:
                next_oid = self.services["next_oid"]
                oid = next_oid(type_, negative)
                operation = Operation(type_ = type_, oid = oid)
                response = self.run_editor(DialogOperation, 
                                           self.db.save, 
                                           operation)
        if response == gtk.RESPONSE_OK:
            self.reload_search()
    
    # Edit the selected item
    def edit(self, *args):
        if self.assert_selected():
            if self.table == TABLE_COMPANIES:
                response = self.run_editor(DialogCompany, self.db.save,
                                           self.selected)
            elif self.table == TABLE_INVENTORY:
                response = self.run_editor(DialogItem, self.db.save,
                                           self.selected)                                           
            elif self.table == TABLE_OPERATIONS:
                try:
                    if self.selected.status == oks.TYPE_STATUS_COMPLETE:
                        raise oks.OperationEditError
                    response = self.run_editor(DialogOperation, self.db.save,
                                               self.selected)
                except oks.OperationEditError, exception:
                    self.show_message(exception.text, exception.secondaryText)
                    response = gtk.RESPONSE_NONE
            if response == gtk.RESPONSE_OK:
                self.reload_search()
                self.on_treeview_cursor_changed()
                    
    # Remove the selected item
    def remove(self, *args):
        if self.assert_selected():
            response = self.show_message(
            "Remover elemento?",
            "Após remover um elemento, ele não poderá ser restaurado.\n"\
            "Note que remover uma operação não alterará o status dela.",
            gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO)
            if response == gtk.RESPONSE_YES:
                type_ = self.selected.TYPE
                row_id = self.selected.row_id
                self.db.delete(type_, row_id = row_id)
                self.reload_search()
                
    # Support for operation status changes directly from the treeview
    def on_operation_status_change(self, cellRenderer, path):
        settings = self.services["settings"]
        response = gtk.RESPONSE_YES
        if settings("ENABLE_INVENTORY_CONTROL"):
            response = self.show_message(
            "Alterar o status da operação?",
            "Os itens da operação serão adicionados ou retirados do estoque.",
            gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO)
        if response == gtk.RESPONSE_YES:
            row_id = self.get_row_id_from_path(path)
            try:
                self.db.toggle_status(oks.OPERATION, row_id)
            except oks.OksException, exception:
                message = "Os problemas abaixo precisam ser corrigidos para "\
                "que o status da operação possa ser alterado:\n\n"
                company = None
                missing = []
                unavailable = []

                operation_reqs = self.services["operation_reqs"]
                reqs = operation_reqs(row_id)
                for req in reqs:
                    req_type, description, quantity = req
                    if req_type == 0:
                        company = description
                    elif req_type == 1 and not quantity:
                        missing.append(description)
                    elif req_type == 1 and quantity:
                        unavailable.append((description, quantity))
                if company:
                    message += "A empresa \"%s\" não está cadastrada.\n" %\
                               company
                    message += "\n"
                if missing:
                    message += "Os seguintes itens não estão cadastrados:\n"
                    for item in missing:
                        message += "• %s\n" % item
                    message += "\n"
                if unavailable:
                    message += "São necessárias as seguintes quantidades "\
                    "adicionais:\n"
                    for item, quantity in unavailable:
                        message += "• %s unidades de %s\n" % (
                        oks.float_to_string(quantity, strip = True), item)
                    message += "\n"
                message = message.strip("\n")
                self.show_message(
                "Não é possível alterar o status",
                message) 
            else:
                self.reload_search()
                
    # Support for transaction status changes directly from the treeview        
    def on_transactionStatusChanged(self, cellRenderer, path):
        row_id = self.get_row_id_from_path(path)
        self.db.toggle_status(oks.TRANSACTION, row_id)
        self.reload_search()
        
    #
    # Special actions
    #
    # Copy an operation
    def copy_operation(self, *args):
        if self.assert_selected():
            operation = self.selected
            negative = False
            if operation.oid < 0:
                negative = True
            next_oid = self.services["next_oid"]
            oid = next_oid(operation.type_, negative)
            new_operation = operation.copy()
            new_operation.oid = oid
            new_operation.date = datetime.date.today()
            if operation.type_ == oks.TYPE_PRODUCTION_OPERATION:
                # Replace the indication of copy
                new_operation.notes = re.sub("Baseada na operação de produção "\
                                             "\d*", 
                                             "",
                                             operation.notes)
                new_operation.notes = ("Baseada na operação de produção %i %s" %
                                      (operation.oid, 
                                       new_operation.notes)).strip()
            else:
                new_operation.notes = operation.notes
                                
            response = self.run_editor(DialogOperation, self.db.save,
                                       new_operation)
            if response == gtk.RESPONSE_OK:
                self.reload_search()

    # Send the items in a production operation to an exchange operation for 
    # finishing
    def finishing(self, *args):
        if self.assert_selected():
            operation = self.selected
            if operation and operation.type_ == oks.TYPE_PRODUCTION_OPERATION:
                new_operation = Operation(type_ = oks.TYPE_EXCHANGE_OPERATION)
                next_oid = self.services["next_oid"]
                settings = self.services["settings"]
                new_operation.oid = next_oid(new_operation.type_)
                new_operation.company = settings("SELF_COMPANY")
                new_operation.notes = "Acabamento da Operação de Produção %s "\
                                      "para %s" % (operation.oid, 
                                                   operation.company)
                for (iter_, rowObject) in operation.input:
                    if rowObject.TYPE == oks.PRODUCTION_ITEM:
                        new_item = ExchangeItem()
                        new_item.name = rowObject.name
                        new_item.quantity = rowObject.quantity
                        new_operation.output.insert(new_item)
                response = self.run_editor(DialogOperation, self.db.save, 
                                           new_operation)
                if response == gtk.RESPONSE_OK:
                    self.reload_search()
                
            else:
                self.show_message("Tipo inválido",
                                  "Somente uma operação de producão pode ser "\
                                  "mandada para acabamento")
    
    # Insert items that don't exist in the invetory but that are required by 
    # the operation
    def resolve_reqs(self, *args):
        if self.assert_selected():
            operation_row_id = self.selected.row_id
            reqs = self.db.get_operation_reqs(operation_row_id)
            for req in reqs:
                req_type, description, quantity = req
                if req_type == 0:
                    company = Company(name=description)
                    self.run_editor(DialogCompany, self.db.save, company)
                elif req_type == 1 and not quantity:
                    item = Item(name=description, quantity=0)
                    self.run_editor(DialogItem, self.db.save, item)
            if reqs == []:
                self.show_message("Nada a cadastrar",
                                  "A empresa e os itens necessários já estão "\
                                  "cadastrados.", gtk.MESSAGE_INFO)
            else:
                self.show_message("Requisitos resolvidos", 
                                  "A empresa e os itens necessários foram "\
                                  "cadastrados.", gtk.MESSAGE_INFO)

    # Save the selected element in a text file
    def save_to_file(self, *args):
        filechooserdialog = gtk.FileChooserDialog(
        None,
        self.window,
        gtk.FILE_CHOOSER_ACTION_SAVE,
        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
        gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        filechooserdialog.set_do_overwrite_confirmation(True)
        # TODO: give this a nicer name
        filechooserdialog.set_current_name("Oks")
        response = filechooserdialog.run()
        if response == gtk.RESPONSE_OK:
            ofile = open(filechooserdialog.get_filename(), "w")
            soh = StringOutputHandler()
            ofile.write(soh.output(self.selected.make_output()))
            ofile.close()
            self.set_statusbar_message("Arquivo salvo")
        filechooserdialog.destroy()

    # Print the selected element
    def print_action(self, *args):
        if self.assert_selected():
            soh = StringOutputHandler()
            content = soh.output(self.selected.make_output())
            settings = self.services["settings"]
          
            print_action = PrintAction(content, 
                                       settings("PRINT_FONT_NAME"),
                                       settings("PRINT_FONT_SIZE"),
                                       set_statusbar_msg = \
                                       self.set_statusbar_message)
            response = print_action.run()
                    
    # Print a label for sending mail to a company
    def print_label(self, *args):
        if self.assert_selected():
            company = self.selected
            sender_name = self.services["settings"]("SELF_COMPANY")
            self_company = self.db.load(oks.COMPANY, name = sender_name)
            if not self_company:
                self.show_message("Remetente não encontrado", "A empresa "\
                                  "configurada como remetente ({0}) não está "\
                                  "cadastrada.".format(sender_name))
                return
            else:
                self_company = self_company[0]
                                
            companies = [("Destinatário", company),]
            if self_company:
                companies.insert(0, ("Remetente", self_company))
                         
            label = ""
            for role, company in companies:
                label += "%s:\n" % role
                label += "    %s\n" % company.full_name
                label += "    %s, %s\n" % (company.address,
                                         company.neighborhood)
                label += "    %s, %s\n" % (company.city, company.state)
                label += "    CEP: %s\n\n" % company.zip_code
                
            print_action = PrintAction(label)
            print_action.run()
                
    #
    # Reports
    #   
    def show_report(self):
        if self.mode == oks.MODE_REPORT:
            report = self.selected.make_output()
            voh = ViewOutputHandler()
            title, content = voh.output(report)
            self.title.set_label(title)
            self.textview.set_value(content)
                    
    def on_report_options_updated(self, field, value):
        if self.selected is not None:
            self.selected.set_option(field.attribute, value)
            self.show_report()
        
    def on_report_type_selected(self, combobox, selected):
        report = self.combobox_report_type.get_value_content()
        if report is None:
            return
        name, report = report
        if report not in self.reports:
            self.reports[report] = report(self.db)
        report = self.reports[report]
        
        # Title
        self.title.set_label(report.NAME)
        
        # Description
        self.label_report_description.set_text(report.DESCRIPTION)

        # Options            
        clear_gtk_container(self.table_report_options)
        self.table_report_options.resize(1, 2)
        self.table_report_options.set_row_spacings(6)
        self.table_report_options.set_col_spacings(6)
        row = 1
        
        # To avoid the destruction of the date fields, keep them in a list
        # If this isn't done, it becomes impossible to work on the field
        # after another one is added, because it gets destroyed in the
        # loop.
        self.report_fields = []
        if report.OPTIONS:
            self.label_report_options.show()
        else:
            self.label_report_options.hide()
        for (option, type_, label, value) in report.OPTIONS:
            self.table_report_options.resize(row + 1, 2)
            if type_ == oks.REPORT_OPTION_BOOL:
                field = CheckButtonField(gtk.CheckButton(label), option)
                field.set_value(report.get_option(option))
                field.connect("new-value", self.on_report_options_updated)
                
                self.table_report_options.attach(field.widget, 
                                                 0, 2, 
                                                 row, row + 1, 
                                                 gtk.EXPAND|gtk.FILL, gtk.FILL)
            elif (type_ == oks.REPORT_OPTION_DATE or
                  type_ == oks.REPORT_OPTION_TEXT):
                label = gtk.Label(label + ": ")
                label.set_alignment(0.0, 0.5)
                
                if type_ == oks.REPORT_OPTION_DATE:
                    field = EntryDate(self, option)
                elif type_ == oks.REPORT_OPTION_TEXT:
                    field = DelayedEntryField(gtk.Entry(), option)
                field.set_value(report.get_option(option))
                field.connect("new-value", self.on_report_options_updated)

                self.table_report_options.attach(label, 
                                                 0, 1, 
                                                 row, row + 1, 
                                                 gtk.FILL, gtk.FILL)
                self.table_report_options.attach(field.widget, 
                                                 1, 2, 
                                                 row, row + 1, 
                                                 gtk.EXPAND|gtk.FILL, gtk.FILL)
                                                 
            row += 1
            self.report_fields.append(field)
        
        # Same actions for all reports
        self.title.enable_actions(True)
        self.title.set_actions(("_Imprimir", self.print_action),
                               ("_Salvar", self.save_to_file))
        
        if report.OPTIONS != []:
            self.vbox_report_options_frame.show_all()
        self.selected = report
        self.show_report()
    
    #
    # Other functions
    #
    def clear_view(self):
        self.title.set_label("")
        self.textview.set_value("")

    def set_statusbar_message(self, msg=None):
        cid = self.statusbar.get_context_id("oks")
        if self.mode == oks.MODE_MAIN:
            mode = "Visão principal"
        elif self.mode == oks.MODE_REPORT:
            mode = "Visão de relatórios"
        self.statusbar.pop(cid)
        if msg is not None:
            self.statusbar.push(cid, "{0} - {1}".format(mode, msg))
        else:
            self.statusbar.push(cid, "{0}".format(mode))
                
    def on_action_show_about_activate(self, widget):
        dialog = self.get_widget("dialog_about")
        dialog.run()
        dialog.hide()
        
    def close(self, *args):
        # FIXME: why double OksWindow.close()?
        Window.close(self, *args)
        self.db_man.close_db()
        Window.close(self)
        
if __name__ == '__main__':
    current_path = sys.path[0]
    db_path = os.path.join(current_path, "db")
    lock_path = os.path.join(current_path, "lock")
    gladeFile = os.path.join(current_path, "gui/oks.glade")
    
    locale.setlocale(locale.LC_ALL, "")
    if os.path.exists(lock_path):
        questionDialog = gtk.MessageDialog(
        None, 
        0, 
        gtk.MESSAGE_QUESTION, 
        gtk.BUTTONS_OK_CANCEL, 
        "Iniciar o programa?")
        questionDialog.format_secondary_text("Oks aparenta já estar aberta.\n"\
        "Deseja iniciar o programa mesmo assim?\n")
        answer = questionDialog.run()
        questionDialog.hide()
        questionDialog.destroy()
        if answer == gtk.RESPONSE_OK:
            os.remove(lock_path)
        else:
            sys.exit(1)
    lock = open(lock_path, "w")
    lock.close()
        
    mainWindow = DialogTable(gladeFile, db_path)
    mainWindow.run()

    os.remove(lock_path)
    sys.exit(0)
