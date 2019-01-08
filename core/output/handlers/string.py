#!/usr/bin/env python
#-*- coding:utf-8 -*-

from core.output import *
from core import utils

# Constants and functions used by the table generator
TABLE_SPACING = 3
string_to_unicode = lambda value, encoding: unicode(str(value), encoding)
    
class OutputHandler:
    def __init__(self):
        pass
    
    def output(self, outputable):
        pass


# StringOutputHandler
def format_String(data):
    return str(data.content)

def format_Float(data, unit=True):
    value = utils.float_to_str(data.content, data.precision, data.strip_zeros)
    if data.unit is not None and unit:
        return "{0} {1}".format(value, data.unit)
    return value

def format_Currency(data, unit=True):
    return utils.float_to_currency(data.content, unit)

def format_Date(data):
    return utils.date_to_str(data.content)

FORMAT = {StringData: format_String,
          IntegerData: format_String,
          FloatData: format_Float,
          DateData: format_Date,
          CurrencyData: format_Currency}


def table_to_string(table):
    if table.is_empty():
        return "---\n"
    string = ""
    columns = []
    data = []
    # Loading the rows and columns
    for n in range(len(table.columns)):
        column = table.columns[n]

        sub = []
        max_width = 0
        
        # Copy the full column contents to restore it later
        full_content = column.content
        for content in table.columns[n].content:
            # Pretend that the column is a common field
            column.content = content
            formatted_content = FORMAT[column.__class__](column)
            if len(formatted_content) > max_width:
                max_width = len(formatted_content)
            sub.append(formatted_content)
        data.append(sub)
        column.content = full_content

        label = column.label
        max_width = max(len(label), max_width) 
        columns.append((label, max_width))
  
    # Make the columns become rows
    data = [[col[n] for col in data] for n in range(len(data[0]))]

    # Writing the columns
    if len(columns) > 1: # Degenerate into a list if there is only one column
        for label, width in columns:
            string += string_to_unicode(label, table.ENCODING).\
                      ljust(width + TABLE_SPACING)
        string += '\n'

    # Writing the rows
    for row in data:
        formatted_row = ""
        for n in range(len(columns)):
            label, width = columns[n]
            formatted_row += string_to_unicode(row[n], table.ENCODING).\
                             ljust(width + TABLE_SPACING)
        string += formatted_row + "\n"

    return string.encode(table.ENCODING)


def _indent(string, level, ilen=4):
    if level == 0:
        return string
    i = 0
    for k in range(level):
        i += ilen/(2**k)
    i = i * " "
    return i + string.replace("\n", "\n" + i).rstrip(i)
  
 
class StringOutputHandler(OutputHandler):
    def __init__(self):
        OutputHandler.__init__(self)

    def _output(self, outputable, parent=None, level=0, string=""):
        if isinstance(outputable, Section) and outputable.children:
            if outputable.title is not None:
                string += _indent(outputable.title, level) + "\n"
            if (parent is not None and
                not (parent.__class__ is Section and
                     parent.is_super_section())):
                level += 1
        elif isinstance(outputable, Data):
            content = FORMAT[outputable.__class__](outputable)
            if outputable.show_empty or not (content == "" or content is None):
                fstr = "{0}: {1}".format(outputable.label, content)
                if isinstance(parent, TableSection):
                    fstr = "-- " + fstr
                string += _indent(fstr, level) + "\n"
        elif outputable.__class__ == Info:
            string += _indent("-- " + outputable.content, level) + "\n"
        elif outputable.__class__ == Table:
            string += _indent(table_to_string(outputable), level)
        
        first = True
        last = None
        if hasattr(outputable, "children"):
            for child in outputable.children:
                if isinstance(child, Section):
                    if isinstance(last, Data):
                        string += "\n"
                    if first:
                        first = False
                    else:
                        string += "\n"
                elif isinstance(last, Section):
                    string += "\n"
                string = self._output(child, outputable, level, string)
                last = child
        return string
    
    def output(self, outputable):
        return self._output(outputable).rstrip("\n")
