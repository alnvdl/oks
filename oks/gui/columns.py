#!/usr/bin/env python
#-*- coding:utf-8 -*-

from gi.repository import Gtk as gtk
from gi.repository import Pango as pango

import core.utils
import oks

class CheckButtonColumn(gtk.TreeViewColumn):
    def __init__(self, title, column, on_toggle=None):
        self.title = title
        self.column = column
        self.cellRenderer = gtk.CellRendererToggle()
        self.cellRenderer.set_property("activatable", True)
        gtk.TreeViewColumn.__init__(self, self.title, self.cellRenderer)
        self.set_cell_data_func(self.cellRenderer, self.set_data)
        if on_toggle:
            self.cellRenderer.connect("toggled", on_toggle)

    def format_data(self, data):
        return data == True

    def set_data(self, treeviewcolumn, cellRenderer, model, rowIter, data):
        data = self.format_data(model[rowIter][treeviewcolumn.column])
        cellRenderer.set_active(data)


class TextColumn(gtk.TreeViewColumn):
    def __init__(self, title, column, sortable = False, ellipsize = False):
        self.title = title
        self.column = column
        self.sortable = sortable
        self.cellRenderer = gtk.CellRendererText()
        gtk.TreeViewColumn.__init__(self, self.title, self.cellRenderer,
                                    text = column)
        if ellipsize:
            self.cellRenderer.set_property("ellipsize", pango.ELLIPSIZE_END)
            self.set_expand(True)
        self.set_expand(True)
        if self.sortable:
            self.set_sort_column_id(self.column)


class IntegerColumn(TextColumn):
    def __init__(self, title, column, sortable = False, ellipsize = False):
        TextColumn.__init__(self, title, column, sortable, ellipsize)


class AdapatedColumn(gtk.TreeViewColumn):
    def __init__(self, title, column, sortable = False, ellipsize = False):
        self.title = title
        self.column = column
        self.sortable = sortable
        self.cellRenderer = gtk.CellRendererText()
        gtk.TreeViewColumn.__init__(self, self.title, self.cellRenderer)
        if ellipsize:
            self.cellRenderer.set_property("ellipsize", pango.ELLIPSIZE_END)
            self.set_expand(True)
        self.set_cell_data_func(self.cellRenderer, self.set_data)
        if self.sortable:
            self.set_sort_column_id(self.column)

    @core.utils.cache
    def format_data(self, data):
        return self.formatting_func(data)

    def set_data(self, treeviewcolumn, cell, model, rowIter, data):
        data = self.format_data(model[rowIter][treeviewcolumn.column])
        cell.set_property("text", data)


class FloatColumn(AdapatedColumn):
    def __init__(self, title, column, sortable = False, ellipsize = False):
        AdapatedColumn.__init__(self, title, column, sortable, ellipsize)

    def formatting_func(self, data):
        return core.utils.float_to_str(float(data), strip = True)


class DateColumn(AdapatedColumn):
    def __init__(self, title, column, sortable = False, ellipsize = False):
        AdapatedColumn.__init__(self, title, column, sortable, ellipsize)

    def formatting_func(self, data):
        return core.utils.internal_date_to_str(data, oks.INTERNAL_DATE_FORMAT)


class CurrencyColumn(AdapatedColumn):
    def __init__(self, title, column, sortable = False, ellipsize = False):
        AdapatedColumn.__init__(self, title, column, sortable, ellipsize)

    def formatting_func(self, data):
        return core.utils.float_to_str(float(data))


class TypeColumn(AdapatedColumn):
    def __init__(self, title, column, types, sortable = False,
                 ellipsize = False):
        AdapatedColumn.__init__(self, title, column, sortable, ellipsize)
        self.types = types

    def formatting_func(self, data):
        return self.types[int(data)]
