#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os.path
import sqlite3
import datetime
import time

from core.db.backends.sqlite import SQLiteBackend as Database
from core.db.models.table import Table
from core.db.completion import AutoCompletion
from core.db.row import RowWithStatus
import oks.db.definition
from oks.elements.company import Company
from oks.elements.item import Item
from oks.elements.operation import Operation
from oks.elements.operation.product import Product
from oks.elements.operation.pitem import ProductionItem
from oks.elements.operation.pitem.rawmaterial import RawMaterial
from oks.elements.operation.eitem import ExchangeItem
from oks.elements.operation.transaction import Transaction
import oks

# Table names
TABLE_COMPANIES = "Companies"
TABLE_INVENTORY = "Inventory"
TABLE_OPERATIONS = "Operations"
TABLE_PRODUCTS = "Products"
TABLE_PRODUCTION_ITEMS = "ProductionItems"
TABLE_RAW_MATERIALS = "RawMaterials"
TABLE_TRANSACTIONS = "Transactions"
TABLE_EXCHANGE_ITEMS = "ExchangeItems"
TABLE_TRANSACTIONS_VIEW = "TransactionsView"
TABLE_SETTINGS = "Settings"

TYPE_MAPPING = [ (oks.COMPANY, Company, TABLE_COMPANIES),
                 (oks.ITEM, Item, TABLE_INVENTORY),
                 (oks.OPERATION, Operation, TABLE_OPERATIONS),
                 (oks.PRODUCT, Product, TABLE_PRODUCTS),
                 (oks.PRODUCTION_ITEM, ProductionItem, TABLE_PRODUCTION_ITEMS,),
                 (oks.RAW_MATERIAL, RawMaterial, TABLE_RAW_MATERIALS),
                 (oks.EXCHANGE_ITEM, ExchangeItem, TABLE_EXCHANGE_ITEMS),
                 (oks.TRANSACTION, Transaction, TABLE_TRANSACTIONS) ]
TYPE_TO_CLASS, TYPE_TO_TABLE, TABLE_TO_TYPE = {}, {}, {}
for type_, class_, table in TYPE_MAPPING:
    TYPE_TO_CLASS[type_] = class_
    TYPE_TO_TABLE[type_] = table
    TABLE_TO_TYPE[table] = type_
TABLE_TO_TYPE[TABLE_TRANSACTIONS_VIEW] = oks.TRANSACTION

DATA_MODEL = { oks.COMPANY: {},
               oks.ITEM: {},
               oks.OPERATION: { oks.PRODUCT: {},
                                oks.PRODUCTION_ITEM: {oks.RAW_MATERIAL: {}},
                                oks.EXCHANGE_ITEM: {},
                                oks.TRANSACTION: {} } }
def get_supported_children(type_, level = DATA_MODEL):
    result = None
    for p in level:
        if type_ == p:
            return list(level[p].keys())
        result = get_supported_children(type_, level[p])
        if result is not None:
            return result


class AppDatabase(Database):
    VERSION = 6

    def __init__(self, dbFile = None):
        create = False
        if not os.path.exists(dbFile) or dbFile == ":memory:":
            create = True

        Database.__init__(self, dbFile)
        if create:
            self.execute_script(oks.db.definition.database_6)
            self.set_app_version(self.VERSION)
        if self.get_app_version() == self.VERSION:
            self.execute_script(oks.db.definition.application_6)
        self.update_tables_info()

        self.changes = {}
        self.connection.create_function("update_hook", 3, self.update_hook)
        self.models = {
        TABLE_COMPANIES: None,
        TABLE_INVENTORY: None,
        TABLE_OPERATIONS: None,
        TABLE_TRANSACTIONS: None,
        TABLE_TRANSACTIONS_VIEW: None}
        for table in list(self.models.keys()):
            self.models[table] = Table(self, table, self.tables[table], True)

        self.settings = {}
        for name, value in list(oks.SETTINGS.items()):
            type_, default = value

            rows = self.get_rows(TABLE_SETTINGS, name=name)
            if rows == []: # Setting not found, reset to default value
                self.settings[name] = default
            else:
                name, value = rows[0]
                try:
                    self.settings[name] = type_(value)
                except:
                    raise oks.SettingValueError(name)

        # Change settings while there's no way to change it through the GUI
        # self.settings["ENABLE_INVENTORY_CONTROL"] = 0
        # self.settings["DEFAULT_TRANSACTION_DEADLINE"] = 28
        # self.settings["PRINT_FONT_NAME"] = "monospace"
        # self.settings["PRINT_FONT_SIZE"] = 10
        # self.settings["SELF_COMPANY"] = ""

        completion = AutoCompletion()
        completion.register("companies:name",
                            self.models[TABLE_COMPANIES], 1)
        completion.register("companies:city",
                            self.models[TABLE_COMPANIES], 6, inline=True)
        completion.register("companies:state",
                            self.models[TABLE_COMPANIES], 7, inline=True)
        completion.register("inventory:item",
                            self.models[TABLE_INVENTORY], 1)
        completion.register("inventory:production_item",
                            self.models[TABLE_INVENTORY], 1,
                            2, oks.TYPE_PRODUCTION_ITEM)
        completion.register("inventory:raw_material",
                            self.models[TABLE_INVENTORY], 1,
                            2, oks.TYPE_RAW_MATERIAL)
        completion.register("transactions:way",
                            self.models[TABLE_TRANSACTIONS], 4, inline=True)

        # Services provided by this class to windows and dialogs.
        # A service should only query the database and never change it.
        self.services = {}
        self.services["completion"] = completion.get
        self.services["next_oid"] = self.get_next_oid
        self.services["operation_reqs"] = self.get_operation_reqs
        self.services["guess_formula"] = self.guess_formula
        self.services["guess_measurements"] = self.guess_measurements
        self.services["settings"] = self.settings.get

        self.load_cache = {}

    def commit(self):
        Database.commit(self)
        callbacks = {
        "INSERT": "row_inserted",
        "UPDATE": "row_updated",
        "DELETE": "row_deleted"}

        # Tell the tables what has changed in the commit
        for ((table, row_id), change_type) in list(self.changes.items()):
            row = self.get_row(table, row_id)
            if row is None: # In case of DELETE
                row = row_id
            callback = getattr(self.models[table], callbacks[change_type])
            callback(row)
            # In case a Transactions row has changed, change TransactionsView
            if table == TABLE_TRANSACTIONS:
                row = self.get_row(TABLE_TRANSACTIONS_VIEW, row_id)
                getattr(self.models[TABLE_TRANSACTIONS_VIEW],
                        callbacks[change_type])(row)

        self.load_cache.clear()
        self.changes.clear()

    def rollback(self):
        self.changes.clear()
        Database.rollback(self)

    # This function is called by SQLite to register the rids of the rows that
    # have been changed in triggers, so that the models can be updated. It is
    # basically used for the Inventory table.
    # This terrible workaround is needed because the Python implementation of
    # SQLite doesn't support the update_hook function.
    def update_hook(self, table, change_type, row_id):
        # TODO: if a DELETE change for a row has been marked, ignore others
        self.changes[(table, row_id)] = change_type

    def load(self, element_type, list_ = False, **kwargs):
        """
        Loads a set of rows from the database based on the given column
        values (kwargs) into a set of row objects of the given type.
        Children rows are loaded as well. If row_id is passed as an argument,
        only return one row (since there should be only one row for any row_id).

        @element_type: the row object type
        @list_: if the function should always return a list
        @kwargs: column values to be loaded
         """
        table = TYPE_TO_TABLE[element_type]
        class_ = TYPE_TO_CLASS[element_type]
        rows = self.get_rows(table, **kwargs)

        elements = []
        for row in rows:
            element = class_()
            element.from_row(row)
            elements.append(element)
            for child_type in get_supported_children(element_type):
                children = self.load(child_type, pid = element.row_id)
                for child in children:
                    element.load_child(child)
        if "row_id" in kwargs and not list_:
            return elements[0]
        return elements

    # Use a cache to speed up reporting. This cache is cleared whenever a
    # commit is made to avoid inconsistencies.
    def cached_load(self, element_type, list_=False, **kwargs):
        table = TYPE_TO_TABLE[element_type]
        if not table in self.load_cache:
            self.load_cache[table] = {}
        row_ids = [row[0] for row in self.get_rows(table, **kwargs)]
        elements = []
        for row_id in row_ids:
            if row_id not in self.load_cache[table]:
                loaded = self.load(element_type,
                                   list_,
                                   **kwargs)
                if type(loaded) != list:
                    loaded = [loaded]
                for new_element in loaded:
                    self.load_cache[table][new_element.row_id] = new_element
            elements.append(self.load_cache[table][row_id])
        if "row_id" in kwargs and not list_:
            return elements[0]
        return elements

    def save(self, element, pid = None, commit=True):
        """
        Saves a row object into the datababse, if possible. If the row
        object has children, they are saved as well.

        @element: the element to be saved
        @pid: parent id, defined by a recursive call in case the element is a
              child
        @commit: whether to commit the changes or not in case of success
        """
        row_id = element.row_id
        if pid:
            element.pid = pid
        row = element.to_row()
        table = TYPE_TO_TABLE[element.TYPE]

        try:
            if not row_id:
                row_id = self.insert(table, row)
                element.row_id = row_id
            else:
                self.update(table, row_id, row)
            for name, container in list(element.children.items()):
                for child in container.deleted:
                    self.delete(child.TYPE, row_id = child.row_id, commit=False)
                for child in container.inserted:
                    self.save(child, pid = element.row_id, commit=False)
                for child in container.updated:
                    self.save(child, pid = element.row_id, commit=False)
        except oks.OksException as exception:
            self.rollback()
            raise exception
        except sqlite3.IntegrityError as exception:
            self.rollback()
            raise oks.InvalidNameError
        else:
            if commit:
                self.commit()
            return row_id

    def delete(self, type_, commit=True, **kwargs):
        """
        Deletes a row at the given row_id from the database, based on the
        given type.

        @type_: the row object type
        @kwargs: column values to be loaded
        """
        table = TYPE_TO_TABLE[type_]
        elements = self.load(type_, list_ = True, **kwargs)
        for element in elements:
            for child_type in get_supported_children(type_):
                children = self.delete(child_type, commit = False,
                                       pid = element.row_id)
        self.delete_rows(table, **kwargs)
        if commit:
            self.commit()

    def toggle_status(self, type_, row_id, commit = True):
        """
        Toggles the status of a RowWithStatus object and that of their
        childen as well.

        @type_: the row object type
        @row_id: the row_id of the row to change the status
        """
        element = self.load(type_, row_id = row_id)
        if not isinstance(element, RowWithStatus):
            raise oks.OksException("the element doesn't have a status property")

        try:
            element.toggle_status()
            self.save(element, commit = False)
            self.apply_rules(element)
            for name, container in list(element.children.items()):
                for (iter_, child) in container:
                    if (isinstance(child, RowWithStatus) and
                        child.CHANGE_STATUS_WITH_PARENT):
                        self.toggle_status(child.TYPE, child.row_id,
                                           commit = False)
        except oks.OksException as exception:
            self.rollback()
            raise exception
        else:
            if commit:
                self.commit()

    def apply_rules(self, element):
        """
        Actions to perfom when the status is changed.

        @element_: the row object
        """

        # If element is an OperationElement, check if it is valid and
        # change the quantities in the Inventory as needed
        if element.TYPE in (oks.PRODUCT,
                            oks.PRODUCTION_ITEM,
                            oks.RAW_MATERIAL,
                            oks.EXCHANGE_ITEM):
            item = self.load(oks.ITEM, name=element.name)

            if not self.settings["ENABLE_INVENTORY_CONTROL"]:
                types_ = {oks.PRODUCT: oks.TYPE_COMMON_ITEM,
                          oks.PRODUCTION_ITEM: oks.TYPE_PRODUCTION_ITEM,
                          oks.RAW_MATERIAL: oks.TYPE_RAW_MATERIAL,
                          oks.EXCHANGE_ITEM: oks.TYPE_COMMON_ITEM}

                if len(item) == 0: # If the item doesn't exist, create it
                    new_item = Item(name=element.name,
                                    quantity=0.0,
                                    type_=types_[element.TYPE])
                    if element.TYPE == oks.PRODUCT:
                        new_item.price = element.price
                    self.save(new_item, commit = False)
                return

            if len(item) == 0:
                raise oks.InvalidItemError
            elif item[0].type_ == oks.TYPE_SERVICE:
                return
            else:
                item = item[0]

            if (element.IO == oks.OUTPUT and
                element.status == oks.TYPE_STATUS_COMPLETE or
                element.IO == oks.INPUT and
                element.status == oks.TYPE_STATUS_INCOMPLETE):
                    item.quantity -= element.quantity
            elif (element.IO == oks.OUTPUT and
                  element.status == oks.TYPE_STATUS_INCOMPLETE or
                  element.IO == oks.INPUT and
                  element.status == oks.TYPE_STATUS_COMPLETE):
                    item.quantity += element.quantity
            if item.quantity < 0:
                raise oks.ItemQuantityError
            self.save(item, commit = False)
        # If element is an Operation, check if the company is valid
        elif element.TYPE == oks.OPERATION:
            # FIXME: find a better way of checking
            company = self.load(oks.COMPANY, name = element.company)
            if len(company) == 0:
                raise oks.InvalidCompanyError

    def close(self):
        # Save the settings
        self.delete_rows(TABLE_SETTINGS)
        for setting, value in list(self.settings.items()):
            self.insert(TABLE_SETTINGS, (setting, str(value)))
        Database.close(self)

    # Services
    # Services are functions provided by the database that give data to the
    # application, but never change the database itself. That is, they provide
    # read-only operations.
    def get_next_oid(self, type_, negative = False):
        (min_, max_) = self.get_min_and_max(TABLE_OPERATIONS, "oid",
                                            type_ = type_)
        if negative:
            if min_ is not None and min_ < 0:
                return min_ - 1
            return -1
        else:
            if max_ is not None:
                return max_ + 1
            return 0

    # Returns the reqs for a status change in an operation.
    # A requirement is a tuple:
    # (reqType, description, quantity)
    # reqType carries the requirement type:
    #   0: Company
    #   1: Item

    # Description holds a description for the missing thing

    # Quantity is optional if there isn't enough to satisfy the operation. If
    # it is None, it means that the item itself doesn't exist.
    def get_operation_reqs(self, operation_row_id):
        reqs = []
        operation = self.load(oks.OPERATION, row_id = operation_row_id)
        newStatus = int(not operation.status)

        # Company
        company = self.load(oks.COMPANY, name = operation.company)
        if not company:
            reqs.append((0, operation.company, None))

        # If we don't inforce the inventory control, stop here
        if not self.settings["ENABLE_INVENTORY_CONTROL"]:
            return reqs

        # Items
        def get_items_list(element, items):
            for name, container in list(element.children.items()):
                for (iter_, child) in container:
                    if child.TYPE in (oks.PRODUCT, oks.PRODUCTION_ITEM,
                                      oks.RAW_MATERIAL, oks.EXCHANGE_ITEM):
                        items.append((child.name, child.IO, child.quantity))
                        child_items = []
                        items.extend(get_items_list(child, child_items))
            return items

        items = []
        items = get_items_list(operation, items)
        for (name, IO, quantity) in items:
            inventoryItem = self.load(oks.ITEM, name = name)
            if not inventoryItem:
                reqs.append((1, name, None))
                continue
            if (inventoryItem and
                inventoryItem[0].type_ == oks.TYPE_SERVICE):
                continue
            else:
                availableQuantity = inventoryItem[0].quantity
                requiredQuantity = quantity
                if (IO == 0 and newStatus == 1 and
                    requiredQuantity > availableQuantity or
                    IO == 1 and newStatus == 0 and
                    requiredQuantity > availableQuantity):
                    reqs.append((1, name, requiredQuantity -
                    availableQuantity))
        return reqs

    def guess_formula(self, description, current_row_id=None):
        formula = []
        density = 2.0
        specification = ProductionItem.get_specification(description)
        rows = self.get_rows_through_child_search(TABLE_OPERATIONS,
                                                  TABLE_PRODUCTION_ITEMS,
                                                  "name_production",
                                                  "%%%s%%" % specification)
        # Sort operations by date
        rows.sort(key = lambda x: x[4])
        while rows != [] and formula == []:
            # Get the row id of the most recent operation (by date)
            row_id = rows.pop()[0]
            operation = self.load(oks.OPERATION, row_id=row_id)
            # Check all the items for a match
            for iter_, item in operation.input:
                # Don't use the item to define its own formula
                if current_row_id == item.row_id:
                    continue
                # If there's a match use the formula
                if (ProductionItem.get_specification(item.name_production) ==
                    specification):
                    density = item.density
                    for iter_, component, in item.formula:
                        formula.append((component.name, component.proportion))
                    break
        return (density, formula)

    def guess_measurements(self, description, current_row_id=None):
        measurements = ProductionItem.get_measurements(description)
        rows = self.get_rows_through_child_search(TABLE_OPERATIONS,
                                                  TABLE_PRODUCTION_ITEMS,
                                                  "name",
                                                  "%%%s%%" % measurements)
        # Sort operations by date
        rows.sort(key = lambda x: x[4])
        while rows != []:
            # Get the row id of the most recent operation (by date)
            row_id = rows.pop()[0]
            operation = self.load(oks.OPERATION, row_id=row_id)
            # Check all the items for a match
            for iter_, item in operation.input:
                # Don't use the item to define its own formula
                if current_row_id == item.row_id:
                    continue
                # If there's a match use the name_production measurements
                if (ProductionItem.get_measurements(item.name) ==
                    measurements):
                    return ProductionItem.get_measurements(item.name_production)
        return None

    # Queries. There is a different query for each one of the main tables.
    # Their results are limited for performance reasons.
    def limit(limit):
        """ Limits the output of a function that returns a list """
        def decorator(function):
            def wrapper(*args):
                return function(*args)[:limit]
            return wrapper
        return decorator

    @limit(256)
    def query_companies(self, search_dict):
        if search_dict["name"]:
            search_dict["name"] = "%%%s%%" % search_dict["name"]
        else:
            del search_dict["name"]

        if search_dict["city"]:
            search_dict["city"] = "%%%s%%" % search_dict["city"]
        else:
            del search_dict["city"]

        return self.query(TABLE_COMPANIES, **search_dict)

    @limit(256)
    def query_inventory(self, search_dict):
        search_dict["name"] = "%%%s%%" % search_dict["name"]
        if search_dict["type_"] == oks.TYPE_ITEMS_ALL:
            del search_dict["type_"]
        return self.query(TABLE_INVENTORY, **search_dict)

    @limit(256)
    def query_operations(self, search_dict):
        type_ = search_dict["type_"]
        if search_dict["type_"] == oks.TYPE_OPERATIONS_ALL:
            del search_dict["type_"]
        search_dict["company"] = "%%%s%%" % search_dict["company"]

        items_dict = {}
        item = search_dict["name"]
        if item:
            items_dict["name"] = "%%%s%%" % item
        del search_dict["name"]

        date = search_dict["date"]
        del search_dict["date"]

        matches = self.query(TABLE_OPERATIONS, reverse = True,
                                      **search_dict)

        if date:
            timedelta = datetime.timedelta(days = 7)
            date_matches = set(self.get_rows_in_range(TABLE_OPERATIONS,
                                                      "date",
                                                      date - timedelta,
                                                      date + timedelta,
                                                      select = "row_id"))
            matches = set(matches)
            matches = list(matches.intersection(date_matches))

        items_tables = (
        TABLE_PRODUCTS,
        TABLE_PRODUCTION_ITEMS,
        TABLE_EXCHANGE_ITEMS)

        if item:
            items_matches = []
            for table in items_tables:
                items_matches.extend(self.query(table, "pid", True,
                                                **items_dict))
            matches = set(matches)
            items_matches = set(items_matches)
            return list(matches.intersection(items_matches))
        else:
            return matches

    @limit(256)
    def query_transactions(self, search_dict):
        company = search_dict["company"]
        transactionType = search_dict["type_"]
        status = search_dict["status"]

        if search_dict["company"]:
            search_dict["company"] = "%%%s%%" % search_dict["company"]
        else:
            del search_dict["company"]
        if search_dict["type_"] == oks.TYPE_TRANSACTIONS_ALL:
            del search_dict["type_"]
        if search_dict["status"] == oks.TYPE_STATUS_ALL:
            del search_dict["status"]
        date = search_dict["date"]
        del search_dict["date"]

        matches = self.query(TABLE_TRANSACTIONS_VIEW, **search_dict)

        if date:
            timedelta = datetime.timedelta(days = 7)
            date_matches = set(self.get_rows_in_range(TABLE_TRANSACTIONS,
                                                      "ddate",
                                                      date - timedelta,
                                                      date + timedelta,
                                                      select = "row_id"))
            matches = set(matches)
            matches = list(matches.intersection(date_matches))

        return matches
