#!/usr/bin/env python
#-*- coding:utf-8 -*-

from core.output import *
from core.report import Report
from core.utils import date_to_str
import oks

class FullCompaniesReport(Report):
    NAME = "Lista de empresas"
    DESCRIPTION = "Listagem com informação completa das empresas."
    def __init__(self, db):
        Report.__init__(self, db)
        
    def make(self):       
        Report.make(self)
        self.data = self.db.cached_load(oks.COMPANY)
        self.data.sort(key = lambda company: company.name)
        
    def make_output(self):
        Report.make_output(self)
        main = Section("full_companies_report", self.NAME)
        
        for company in self.data:
            main.add_child(company.make_output())
        
        return main

        
class CompactCompaniesReport(Report):    
    NAME = "Lista compacta de empresas"
    DESCRIPTION = "Listagem compacta das empresas, com apenas nome e telefone."
    OPTIONS = [("customers", oks.REPORT_OPTION_BOOL, 
                "Incluir clientes", True),
                
               ("suppliers",oks.REPORT_OPTION_BOOL,
                "Incluir fornecedores", True),
                
               ("city", oks.REPORT_OPTION_TEXT,
                "Filtrar por cidade", ""),]
    
    def __init__(self, db):
        Report.__init__(self, db)
        
    def make(self):
        Report.make(self)
        companies = []
        if self.customers:
            companies.extend(self.db.cached_load(oks.COMPANY,
                                            type_=oks.TYPE_CUSTOMER_COMPANY,
                                            city="~%%%s%%" % self.city))
        if self.suppliers:
            companies.extend(self.db.cached_load(oks.COMPANY,
                                            type_=oks.TYPE_SUPPLIER_COMPANY,
                                            city="~%%%s%%" % self.city))
        if self.customers or self.suppliers:
            companies.extend(self.db.cached_load(oks.COMPANY,
                                            type_=oks.TYPE_CUSTOMER_AND_SUPPLIER_COMPANY,
                                            city="~%%%s%%" % self.city))
                                                                                                                                         
        for company in companies:
            self.data.append([company.name, company.phone])            
        self.data.sort(key = lambda row: row[0]) # Sort by name
        
    def make_output(self):
        Report.make_output(self)
        return TableSection("compact_companies_report", self.NAME,
                            (StringData("name", "Nome"),
                             StringData("phone", "Telefone")),
                            self.data, self.bits)


class MostImportantCompanies(Report):
    NAME = "Clientes mais importantes"
    DESCRIPTION = "Listagem de empresas ordenedadas pelos valores consumidos "\
                  "em um dado período."
    OPTIONS = oks.DATE_RANGE_OPTIONS
              
    def __init__(self, db):
        Report.__init__(self, db)
                
    def make(self):        
        Report.make(self)
        
        operations = self.db.cached_load(oks.OPERATION,
                                         type_=oks.TYPE_SALE_OPERATION,
                                         date=(self.start_date, self.end_date),
                                         status=oks.TYPE_STATUS_COMPLETE)
                                  
        companies = {}
        for operation in operations:
            value = operation.get_total_value()
            try:
                companies[operation.company] += value
            except KeyError:
                companies[operation.company] = value
                
        self.data = list(companies.items())
        self.data.sort(key = lambda company_value: company_value[1])
                            
    def make_output(self):
        Report.make_output(self)
        title = "{0} - {1} a {2}".format(self.NAME, 
                                         date_to_str(self.start_date),
                                         date_to_str(self.end_date))
        return TableSection("most_important_companies", title,
                            (StringData("company", "Empresa"),
                             CurrencyData("sales", "Vendas", unit="R$")),
                            self.data, self.bits)
