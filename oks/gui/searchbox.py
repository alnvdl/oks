#!/usr/bin/env python
#-*- coding:utf-8 -*-

import gtk
import gobject

class SearchBox(gtk.Table):
    __gsignals__ = { "search-updated": (gobject.SIGNAL_RUN_LAST, 
                                        gobject.TYPE_NONE, 
                                        (gobject.TYPE_PYOBJECT,)) }

    def __init__(self, autoUpdate = False):
        gtk.Table.__init__(self, 1, 2)
        self.autoUpdate = autoUpdate
        self.set_row_spacings(6)
        self.set_col_spacings(12)
        self.fields = []
        
    def add_field(self, labelText, fieldWidget):
        self.fields.append(fieldWidget)
        if self.autoUpdate:
            fieldWidget.connect("new-value", self.emit_search_updated)
        else:
            if gobject.signal_lookup("activate", fieldWidget.get_widget()):
                fieldWidget.get_widget().connect("activate", 
                                                 self.emit_search_updated)
            
        label = gtk.Label(labelText)
        label.set_alignment(0.0, 0.5)
        
        currentNRows = self.get_property("n-rows")
        nColumns = self.get_property("n-columns")
        
        self.attach(label, nColumns - 2, nColumns - 1, currentNRows - 1, 
                    currentNRows, gtk.FILL)
        self.attach(fieldWidget.widget, nColumns - 1, nColumns - 0, 
                    currentNRows - 1, currentNRows, gtk.EXPAND|gtk.FILL)
        self.resize(currentNRows + 1, nColumns)
        self.show_all()
    
    def grab_focus(self, n = 0):
        self.fields[n].get_widget().grab_focus()
        
    def get_search(self):
        searchDict = {}
        for field in self.fields:
            searchDict[field.get_attribute()] = field.get_value()
        return searchDict
        
    def emit_search_updated(self, *args):
        self.emit("search-updated", self.get_search())
        
    def clear(self):
        for field in self.fields:
            field.clear()
        
    def reset(self):
        for child in self.get_children():
            child.hide_all()
            self.remove(child)
            del child
        self.fields = []
        self.resize(1, 2)
