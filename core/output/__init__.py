#!/usr/bin/env python
#-*- coding:utf-8 -*-

__all__ = ("Section",
           "Data",
           "StringData",
           "IntegerData", 
           "FloatData", 
           "DateData", 
           "CurrencyData",
           "Info",
           "Table",
           "TableSection")

class Outputable:
    def __init__(self, id):
        self.id = id


# Section
class Section(Outputable):
    def __init__(self, id, title=None, *children):
        Outputable.__init__(self, id)
        self.title = title
        self.children = list(children)

    def add_child(self, child):
        self.children.append(child)
    
    def remove_child(self, id):
        for child in self.children:
            if child.id == id:
                self.children.remove(child)

    def get_child(self, id):
        for child in self.children:
            if child.id == id:
                return child

    def is_super_section(self):
        for child in self.children:
            if child.__class__ != Section or child.__class__ != Info:
                return False
        return True


class Data(Outputable):
    def __init__(self, id, label, content=None, unit=None, show_empty=False):
        Outputable.__init__(self, id)
        self.label = label
        self.content = content
        self.unit = unit
        self.show_empty = show_empty


class StringData(Data):
    def __init__(self, id, label, content=None, show_empty=False):
        Data.__init__(self, id, label, content, None, show_empty)


class IntegerData(Data):
    def __init__(self, id, label, content=None, unit=None, show_empty=False):
        Data.__init__(self, id, label, content, unit, show_empty)


class FloatData(Data):
    def __init__(self, id, label, content=None, unit=None, show_empty=False,
                 precision=2, strip_zeros=False):
        Data.__init__(self, id, label, content, unit, show_empty)
        self.precision = precision
        self.strip_zeros = strip_zeros


class DateData(Data):
    def __init__(self, id, label, content=None, show_empty=False, format=None):
        Data.__init__(self, id, label, content, None, show_empty)
        self.format = format


class CurrencyData(Data):
    def __init__(self, id, label, content=None, unit=None, show_empty=False, 
                 precision=2):
        Data.__init__(self, id, label, content, unit, show_empty)
        self.precision = precision


# Info
class Info(Outputable):
    def __init__(self, id, content):
        Outputable.__init__(self, id)
        self.content = content


class Table(Outputable):
    ENCODING = "utf-8"
    
    def __init__(self, id, columns, rows=None):
        Outputable.__init__(self, id)
        for column in columns:
            column.content = []
        self.columns = columns 
        
        if rows is not None:
            for row in rows:
                self.add_row(row)        

    def add_row(self, row):
        for n in range(len(self.columns)):
            self.columns[n].content.append(row[n])

    def remove_row(self, n):
        for column in self.columns:
            del column[n]
    
    def is_empty(self):
        for column in self.columns:
            if column.content:
                return False
        return True
            
class TableSection(Section):
    def __init__(self, id, title, columns, rows=None, footnotes=None):
        Section.__init__(self, id, title)

        self.table = Table("%s_table" % self.id, columns, rows)
        self.add_row = self.table.add_row
        self.remove_row = self.table.remove_row
        self.is_empty = self.table.is_empty
        self.children = [self.table]
        
        if footnotes != None:
            for footnote in footnotes:
                self.add_child(footnote)
                
    def add_child(self, child):
        if isinstance(child, Data) or isinstance(child, Info):
            Section.add_child(self, child)

    def remove_child(self, id):
        for child in children:
            if (isinstance(child, Data) or isinstance(child, Info) and 
                child.id == id):
                Section.remove_child(self, id)
