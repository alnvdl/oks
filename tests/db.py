#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

import oks
from oks.db.app import AppDatabase
from oks.elements.company import Company
from oks.elements.item import Item
from oks.elements.operation import Operation
from oks.elements.operation.product import Product
from oks.elements.operation.pitem import ProductionItem
from oks.elements.operation.pitem.rawmaterial import RawMaterial
from oks.elements.operation.eitem import ExchangeItem
from oks.elements.operation.transaction import Transaction

COMPANY_1 = "Company"
COMPANY_2 = "Company 2"
 
ITEM_1 = "Item"
ITEM_2 = "Item 2"
    
RAW_MATERIAL_1 = "Raw Material"
RAW_MATERIAL_2 = "Raw Material 2"

PRODUCTION_ITEM_1 = "RT 123x45x6"
PRODUCTION_ITEM_2 = "RT 120x42x3"

    
class OksTestCase(unittest.TestCase):
    """ Unit test for the database triggers """
    def setUp(self):
        self.db = AppDatabase(":memory:")
        
    def tearDown(self):
        self.db.close()          
        

class CompaniesTest(OksTestCase):    
    def testBlankCompanyName(self):
        """ Blank names for companies should raise an error """        
        company = Company(name = "")
        self.assertRaises(oks.InvalidNameError, self.db.save, company)

    def testExistingCompanyName(self):
        """ Using existing names for companies should raise an error """
        company = Company(name = COMPANY_1)
        self.db.save(company)
        
        company = Company(name = COMPANY_1)
        self.assertRaises(oks.InvalidNameError, self.db.save, company)   
       
    def testCompanyNameChange(self):
        """ When a company is renamed, operations related to this company 
        should be updated """
        company = Company(name = COMPANY_1)
        company_row_id = self.db.save(company)
        
        operation = Operation(company = COMPANY_1)
        operation_row_id = self.db.save(operation)
        
        company = self.db.load(oks.COMPANY, row_id = company_row_id)
        company.name = COMPANY_2
        self.db.save(company)
        
        operation = self.db.load(oks.OPERATION, row_id = operation_row_id)
        self.assertEqual(operation.company, COMPANY_2)

class InventoryTest(OksTestCase):    
    def testeBlankItemName(self):
        """ Blank names for items of any type should raise an error """
        item = Item()
        self.assertRaises(oks.InvalidNameError, self.db.save, item)
        
    def testExistingItemName(self):
        """ Using existing names for items should raise an error """
        item = Item(name = ITEM_1)
        self.db.save(item)
        
        item = Item(name = ITEM_1)
        self.assertRaises(oks.InvalidNameError, self.db.save, item)
        
    def testItemNameChange(self):
        """ When any item is renamed, the related operation and production 
        items should be renamed too """
        company = Company(name = COMPANY_1)
        company_row_id = self.db.save(company)
        
        item = Item(name = ITEM_1)
        item_row_id = self.db.save(item)
    
        operation = Operation(company = COMPANY_1)
        
        product = Product(name = ITEM_1)
        production_item = ProductionItem(name = ITEM_1)
        raw_material = RawMaterial(name = ITEM_1)
        exchange_item = ExchangeItem(name = ITEM_1)
        
        production_item.formula.insert(raw_material)
        operation.output.insert(product)
        operation.output.insert(production_item)
        operation.output.insert(exchange_item)
        operation_row_id = self.db.save(operation)
        
        item = self.db.load(oks.ITEM, row_id = item_row_id)
        item.name = ITEM_2
        item_row_id = self.db.save(item)
               
        operation = self.db.load(oks.OPERATION, row_id = operation_row_id)
        
        self.assertEqual(operation.output[0][0].name, ITEM_2)
        self.assertEqual(operation.output[1][0].name, ITEM_2)
        self.assertEqual(operation.output[1][0].formula[0][0].name, ITEM_2)
        self.assertEqual(operation.output[2][0].name, ITEM_2)
                 
class OperationsTest(OksTestCase):
    def testInvalidCompanyOnInsert(self):
        """ A operation with an invalid company should not be able to be marked 
        as concluded """
        company = Company(name = COMPANY_1)
        company_row_id = self.db.save(company)
        
        operation = Operation(company = COMPANY_2)
        operation_row_id = self.db.save(operation)
        
        self.assertRaises(oks.InvalidCompanyError, self.db.toggle_status, 
                          oks.OPERATION, operation_row_id)
    
# FIXME: bring these tests back
#    def testInsertingCompletedOperation(self):
#        """ A completed operation should not be inserted """
#        company = Company(name = COMPANY_1)
#        company_row_id = self.db.save(company)

#        operation = Operation(company = COMPANY_1)
#        operation.status = 1
#        self.assertRaises(oks.BadStatusError, self.db.save_operation, operation)
        

#    def testUpdatingCompletedOperation(self):
#        """ When the status is 1, the only field that can change is the status 
#        field, and any changes should be ignored """
#        company = Company(name = COMPANY_1)
#        self.db.save(company)

#        company = Company(name = COMPANY_2)
#        self.db.save(company)
#                        
#        operation = Operation(company = COMPANY_1)
#        operation_row_id = self.db.save_operation(operation)
#                        
#        operation = self.db.load_operation(operation_row_id)
#        operation.status = 1
#        operation.company = COMPANY_2
#        operation_row_id = self.db.save_operation(operation)

#        operation = self.db.load_operation(operation_row_id)        
#        self.assertEquals(operation.company, COMPANY_1)
#        
    def testInvalidProductOnUpdate(self):
        """ An operation item of any type should not be updated if it does not 
        exist """
        company = Company(name = COMPANY_1)
        company_row_id = self.db.save(company)
        
        item = Item(name = ITEM_1)
        item_row_id = self.db.save(item)
        
        operation = Operation(company = COMPANY_1)
        product = Product(name = ITEM_1)
        operation.input.insert(product)
        operation_row_id = self.db.save(operation)
        
        operation = self.db.load(oks.OPERATION, row_id = operation_row_id)
        product = operation.input[0][0]
        product.name = ITEM_2
        operation.input.update(product, operation.input[0].iter)
        operation_row_id = self.db.save(operation)
            
        self.assertRaises(oks.InvalidItemError, self.db.toggle_status, 
                          oks.OPERATION, operation_row_id)
        
    def testInvalidQuantity(self):
        """ Trying to take a given quantity from the Inventory that is larger 
        than what is available should raise an error """
        company = Company(name = COMPANY_1)
        company_row_id = self.db.save(company)
        
        item = Item(name = ITEM_1, quantity = 1)
        item_row_id = self.db.save(item)
        
        operation = Operation(company = COMPANY_1)
        product = Product(name = ITEM_1, quantity = 2)
        operation.output.insert(product)
        operation_row_id = self.db.save(operation)
        
        self.assertRaises(oks.ItemQuantityError, self.db.toggle_status, 
                          oks.OPERATION, operation_row_id)
        
    def testOperationInventoryIO(self):
        """
        Products, ProductionItems, RawMaterials and ExchangeItems should
        add to the Inventory when inside the input and subtract from it when
        inside the output
        """
        company = Company(name = COMPANY_1)
        self.db.save(company)
        
        item = Item(name = ITEM_1, quantity = 10)
        item_row_id = self.db.save(item)
        
        item2 = Item(name = ITEM_2, quantity = 100)
        item2_row_id = self.db.save(item2)
        
        operation = Operation(company = COMPANY_1,
                                          type_ = oks.TYPE_SALE_OPERATION)
        
        product = Product(name = ITEM_1, quantity = 3)
        product2 = Product(name = ITEM_2, quantity = 27)
        
        operation.output.insert(product)
        operation.input.insert(product2)
        
        operation_row_id = self.db.save(operation)
        
        self.db.toggle_status(oks.OPERATION, operation_row_id)
        
        self.assertEqual(self.db.load(oks.ITEM, row_id = item_row_id).quantity, 7.0)
        self.assertEqual(self.db.load(oks.ITEM, row_id = item2_row_id).quantity, 127.0)
        
        self.db.toggle_status(oks.OPERATION, operation_row_id)
        
        self.assertEqual(self.db.load(oks.ITEM, row_id = item_row_id).quantity, 10.0)
        self.assertEqual(self.db.load(oks.ITEM, row_id = item2_row_id).quantity, 100.0)
                
    def testProductionOperationStatusChange(self):
        """ A production operation should have its items added from the 
        inventory when concluded and put back when unconcluded. The raw 
        materials used in it should follow the reverse path"""
        company = Company(name = COMPANY_1)
        company_row_id = self.db.save(company)

        raw_material = Item(name = RAW_MATERIAL_1, quantity = 100)
        raw_material_row_id = self.db.save(raw_material)
        
        production_item = Item(name = PRODUCTION_ITEM_1, 
                                          quantity = 3)
        production_item_row_id = self.db.save(production_item)
        
        operation = Operation(company = COMPANY_1, 
                                          type_ = oks.TYPE_PRODUCTION_OPERATION)
        
        production_item = ProductionItem(name = PRODUCTION_ITEM_1,
                                         quantity = 10,
                                         name_production = PRODUCTION_ITEM_1,
                                         quantity_production = 10)
        volume = ProductionItem.calculate_volume(production_item.name)
        production_item.volume = volume
        raw_material = RawMaterial(name = RAW_MATERIAL_1, 
                                   proportion = 50)
        production_item.formula.insert(raw_material)
        operation.input.insert(production_item)
        
        operation_row_id = self.db.save(operation)
        
        self.db.toggle_status(oks.OPERATION, operation_row_id)
        
        production_item = self.db.load(oks.ITEM, row_id = production_item_row_id)
        raw_material = self.db.load(oks.ITEM, row_id = raw_material_row_id)
        self.assertEqual(production_item.quantity, 13.0)
        self.assertEqual(raw_material.quantity, 88.797956316250989)
                
        self.db.toggle_status(oks.OPERATION, operation_row_id)
        
        production_item = self.db.load(oks.ITEM, row_id = production_item_row_id)
        raw_material = self.db.load(oks.ITEM, row_id = raw_material_row_id)
        self.assertEqual(production_item.quantity, 3.0)
        self.assertEqual(raw_material.quantity, 100.0)
        
    def testProductionItemUpdate(self):
        """ A production item formula components should be taken from the 
        inventory, but when the item changes, the formula must be updated too """
        company = Company(name = COMPANY_1)
        company_row_id = self.db.save(company)

        raw_material = Item(name = RAW_MATERIAL_1, quantity = 100)
        raw_material_row_id = self.db.save(raw_material)
        
        raw_material2 = Item(name = RAW_MATERIAL_2, quantity = 130)
        raw_material2_row_id = self.db.save(raw_material2)
        
        production_item = Item(name = PRODUCTION_ITEM_1, 
                               quantity = 3)
        production_item_row_id = self.db.save(production_item)
        
        operation = Operation(company = COMPANY_1, 
                                          type_ = oks.TYPE_PRODUCTION_OPERATION)
        
        production_item = ProductionItem(name = PRODUCTION_ITEM_1, 
                                         quantity = 10,
                                         name_production = PRODUCTION_ITEM_1,
                                         quantity_production = 10)
        volume = ProductionItem.calculate_volume(production_item.name)
        production_item.volume = volume
        raw_material = RawMaterial(name = RAW_MATERIAL_1, 
                                   proportion = 60)
        raw_material2 = RawMaterial(name = RAW_MATERIAL_2, 
                                    proportion = 10)
                                          
        production_item.formula.insert(raw_material)
        production_item.formula.insert(raw_material2)
        operation.input.insert(production_item)

        operation_row_id = self.db.save(operation)
        
        self.db.toggle_status(oks.OPERATION, operation_row_id)
        
        production_item = self.db.load(oks.ITEM, row_id = production_item_row_id)
        raw_material = self.db.load(oks.ITEM, row_id = raw_material_row_id)
        raw_material2 = self.db.load(oks.ITEM, row_id = raw_material2_row_id)
        self.assertEqual(production_item.quantity, 13.0)
        self.assertEqual(raw_material.quantity, 90.398248271072276)
        self.assertEqual(raw_material2.quantity, 128.3997080451787)
            
        self.db.toggle_status(oks.OPERATION, operation_row_id)

        production_item = self.db.load(oks.ITEM, row_id = production_item_row_id)
        raw_material = self.db.load(oks.ITEM, row_id = raw_material_row_id)
        raw_material2 = self.db.load(oks.ITEM, row_id = raw_material2_row_id)
        self.assertEqual(production_item.quantity, 3.0)
        self.assertEqual(raw_material.quantity, 100.0)
        self.assertEqual(raw_material2.quantity, 130.0)
        
        operation = self.db.load(oks.OPERATION, row_id = operation_row_id)
        production_itemRowIter = operation.input.get_iter_first()
        production_item = operation.input.get_object(production_itemRowIter)
        componentRowIter = production_item.formula.get_iter_first()
        production_item.formula.delete(componentRowIter)
        production_item.formula.update_components()
        operation.input.update(production_item, production_itemRowIter)
        operation_row_id = self.db.save(operation)
        
        self.db.toggle_status(oks.OPERATION, operation_row_id)
        
        production_item = self.db.load(oks.ITEM, row_id = production_item_row_id)
        raw_material = self.db.load(oks.ITEM, row_id = raw_material_row_id)
        raw_material2 = self.db.load(oks.ITEM, row_id = raw_material2_row_id)
        self.assertEqual(production_item.quantity, 13.0)
        self.assertEqual(raw_material.quantity, 100.0)
        self.assertEqual(raw_material2.quantity, 118.79795631625099)        
        
    def testInvalidItemCannotBeSaved(self):
        """ An item that doesn't exist should raise an exception when trying to 
        change its status """
        company = Company(name = COMPANY_1)
        self.db.save(company)
        
        item = Item(name = ITEM_1)
        item_row_id = self.db.save(item)

        operation = Operation(company = COMPANY_1)
        product = Product(name = ITEM_2)
        operation.output.insert(product)
        operation_row_id = self.db.save(operation)
        
        self.assertRaises(oks.InvalidItemError, self.db.toggle_status,
                          oks.OPERATION, operation_row_id)
        

