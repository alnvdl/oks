#!/usr/bin/env python
#-*- coding:utf-8 -*-

import datetime

from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject
from gi.repository import Pango as pango

class Field(gobject.GObject):
    """ A Field object provides a wrapper around a gtk.Widget so that some
    convinence methods can be defined """
    __gsignals__ = {
    "new-value": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
    }
    def __init__(self, widget, attribute = None):
        gobject.GObject.__init__(self)
        self.widget = widget # Read-only
        self.attribute = attribute # Read-only
        self.defaultValue = None

    def get_widget(self):
        return self.widget

    def get_attribute(self):
        return self.attribute

    def get_widget(self):
        return self.widget

    def get_value(self):
        raise NotImplementedError

    def set_value(self, value):
        raise NotImplementedError

    def set_sensitive(self, sensitive):
        self.widget.set_sensitive(sensitive)

    def set_completion(self, model, column):
        raise NotImplementedError

    def emit_new_value(self, *args):
        self.emit("new-value", self.get_value())

    def clear(self):
        self.set_value(self.get_defaultValue())

    def get_defaultValue(self):
        return self.defaultValue

    def set_defaultValue(self, defaultValue):
        self.defaultValue = defaultValue


class LabelField(Field):
    def __init__(self, widget, attribute = None):
        Field.__init__(self, widget, attribute)

    def get_value(self):
        return self.widget.get_text()

    def set_value(self, value):
        self.widget.set_text(value)


class EntryField(Field):
    def __init__(self, widget, attribute = None):
        Field.__init__(self, widget, attribute)
        self.widget.connect("changed", self.emit_new_value)
        self.set_defaultValue("")

    def get_value(self):
        return self.widget.get_text()

    def set_value(self, value):
        self.widget.set_text(value)

    def set_completion(self, entryCompletion):
        self.widget.set_completion(entryCompletion)


class DelayedEntryField(Field):
    def __init__(self, widget, attribute = None):
        Field.__init__(self, widget, attribute)
        self.timeout = 0
        self.widget.connect("changed", self.delayed_emit_new_value)
        self.set_defaultValue("")

    def delayed_emit_new_value(self, *args):
        if self.timeout != 0:
            gobject.source_remove(self.timeout)
        self.timeout = gobject.timeout_add(500, self.emit_new_value)

    def get_value(self):
        return self.widget.get_text()

    def set_value(self, value):
        self.widget.set_text(value)

    def set_completion(self, entryCompletion):
        self.widget.set_completion(entryCompletion)


class SpinButtonField(Field):
    def __init__(self, widget, attribute = None):
        Field.__init__(self, widget, attribute)
        self.widget.connect("value-changed", self.emit_new_value)
        self.set_defaultValue(0)

    def get_value(self):
        self.widget.update()
        return float(self.widget.get_value())

    def set_value(self, value):
        self.widget.set_value(float(value))
        self.widget.update()


class CheckButtonField(Field):
    def __init__(self, widget, attribute = None):
        Field.__init__(self, widget, attribute)
        self.widget.connect("toggled", self.emit_new_value)
        self.set_defaultValue(False)


    def get_value(self):
        return self.widget.get_active()

    def set_value(self, value):
        self.widget.set_active(value)


class ComboBoxField(Field):
    def __init__(self, widget, attribute = None, *args):
        Field.__init__(self, widget, attribute)
        self.handler_id = self.widget.connect("changed", self.emit_new_value)
        if not args:
            columns = [gobject.TYPE_STRING]
        else:
            columns = args
        self.model = gtk.ListStore(*columns)
        widget.set_model(self.model)
        cell = gtk.CellRendererText()
        self.widget.pack_start(cell, True)
        self.widget.add_attribute(cell, "text", 0)

    def set_options(self, *options):
        # Avoid unnecessary signal emissions
        self.widget.disconnect(self.handler_id)
        self.model.clear()
        for option in options:
            if type(option) not in (list, tuple):
                option = [option]
            self.model.append(option)
        # Reestablish signal emissions
        self.handler_id = self.widget.connect("changed", self.emit_new_value)

    def get_value(self):
        return self.widget.get_active()

    def set_value(self, value):
        self.widget.set_active(value)

    def get_value_content(self):
        active = self.get_value()
        if active != -1:
            return list(self.model[active])
        return None

class TextViewField(Field):
    def __init__(self, widget, attribute = None):
        Field.__init__(self, widget, attribute)

    def get_value(self):
        textBuffer = self.widget.get_buffer()
        start, end = textBuffer.get_start_iter(), textBuffer.get_end_iter()
        return textBuffer.get_text(start, end, True)

    def set_value(self, value):
        textBuffer = self.widget.get_buffer()
        textBuffer.set_text(value)

    def set_font(self, fontDescription):
        self.widget.modify_font(pango.FontDescription(fontDescription))


class TreeViewField(Field):
    def __init__(self, widget, attribute = None):
        Field.__init__(self, widget, attribute)
        self.model = self.get_value()

    def get_value(self):
        return self.widget.get_model()

    def set_value(self, value):
        self.model = value
        return self.widget.set_model(value)

    def get_model(self):
        """ An alias for get_value in a TreeView Field """
        return self.get_value()
