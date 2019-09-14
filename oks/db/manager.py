#!/usr/bin/env python
#-*- coding:utf-8 -*-

import datetime
import shutil
import os
import os.path

from core.db.backends.sqlite import SQLiteBackend as Database
from oks.db.app import AppDatabase
import oks.db.definition

VERSIONS = [5,6]

class DatabaseManager:
    NEW_PATH = "new"

    def __init__(self, path):
        self.path = path
        
    def open_db(self):
        if os.path.exists(self.path):
            tmp_db = Database(self.path)
            version = tmp_db.get_app_version()
            while version != VERSIONS[-1]:
                convert = getattr(self, "convert_from_%i_to_%i" % (version, 
                                                                   version + 1))
                tmp_db = convert(tmp_db, self.NEW_PATH)
                version = tmp_db.get_app_version()
            tmp_db.close()
        self.db = AppDatabase(self.path)

    def convert_from_5_to_6(self, old_db, new_path):
        new_db = Database(new_path)
        new_db.execute_script(oks.db.definition.database_6)
        new_db.set_app_version(6)
        new_db.update_tables_info()
        
        companies = old_db.get_rows("Companies")
        for row in companies:
            new_db.insert("Companies", row)
        
        inventory = old_db.get_rows("Inventory")
        for row in inventory:
            row = list(row)
            row.insert(3, 0) # Unit column
            new_db.insert("Inventory", tuple(row))
        
        previous_date = "1970-1-1"
        operations = old_db.get_rows("Operations")
        for row in operations:
            # Fix a weird bug that caused null dates
            # Assume that the date is the same as the previous operation's date
            if row[4] is None:
                row = list(row)
                row[4] = previous_date
                row = tuple(row)
            else:
                previous_date = row[4]
            new_db.insert("Operations", row)
        
        products = old_db.get_rows("Products")
        for row in products:
            new_db.insert("Products", row)
            
        production_items = old_db.get_rows("ProductionItems")
        for row in production_items:
            # Add the name_production and quantity_production fields based on
            # the old name and quantity fields
            row = list(row)
            name_production = row[3]
            quantity_production = row[4]
            row.insert(5, name_production)
            row.insert(6, quantity_production)
            new_db.insert("ProductionItems", tuple(row))

        raw_materials = old_db.get_rows("RawMaterials")
        for row in raw_materials:
            new_db.insert("RawMaterials", row)

        exchange_items = old_db.get_rows("ExchangeItems")
        for row in exchange_items:
            new_db.insert("ExchangeItems", row)

        transactions = old_db.get_rows("Transactions")
        for row in transactions:
            new_db.insert("Transactions", row)
        
        old_db.close()
        new_db.close()
        os.remove(self.path)
        os.rename(new_path, self.path)
        return Database(self.path)
        
    def export_db(self, destination):
        self.close_db()
        shutil.copyfile(self.path, destination)
        self.open_db()
        
    def import_db(self, source):
        self.close_db()
        if source:
            shutil.copyfile(source, self.path)
        self.open_db()
            
    def close_db(self):
        self.db.close()
