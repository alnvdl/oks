#!/usr/bin/env python
#-*- coding:utf-8 -*-

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as gtk

# from gi.repository import Gtk as gtk

import core.db

class InternalModel(gtk.ListStore):
    """ A InternalModel holds a set of objects that are created based on row in
    the SQLite model. These objects represent an Operation. """
    def __init__(self, IO = 0):
        gtk.ListStore.__init__(self, object)
        self.IO = IO
        self.inserted = []
        self.updated = []
        self.deleted = []

    def get_object(self, iter_):
        return self.get_value(iter_, 0)

    def insert(self, rowObject, type_=core.db.NEW):
        # Registers the rows if they were created to be added to the database
        if type_ in (core.db.NEW, core.db.COPY):
            self.inserted.append(rowObject)
            rowObject.IO = self.IO
        return gtk.ListStore.insert(self, -1, [rowObject])

    def update(self, newRowObject, iter_):
        oldRowObject = self.get_object(iter_)
        self.set(iter_, 0, newRowObject)
        # If the element was inserted but it wasn't in the database
        if oldRowObject in self.inserted:
            self.inserted.remove(oldRowObject)
            self.inserted.append(newRowObject)
        # If the element was updated but the update wasn't in the database
        elif oldRowObject in self.updated:
            self.updated.remove(oldRowObject)
            self.updated.append(newRowObject)
        else:
            self.updated.append(newRowObject)

    def delete(self, iter_):
        rowObject = self.get_object(iter_)
        # FIXME: why is it removing from self.inserted so many times?
        if rowObject in self.inserted: # If the element was inserted but it wasn't in the database
            self.inserted.remove(rowObject)
        else: # If the element was already registered in the database
            self.deleted.append(rowObject)
        # If it was inserted or updated, remove it from there
        while rowObject in self.inserted:
            self.inserted.remove(rowObject)
        while rowObject in self.updated:
            self.updated.remove(rowObject)
        self.remove(iter_)

    def __iter__(self):
        objects = []
        for i in range(len(self)):
            objects.append((self[i].iter, self.get_object(self[i].iter)))
        return iter(objects)

    def clear(self):
        for iter_, element in self:
            self.delete(iter_)


class FilteredInternalModel:
    """ A wrapper for the InternalModel that adapts the attributes of the
    objects as columns for a TreeView """

    def __init__(self, baseModel, *columns):
        self.baseModel = baseModel
        self.filteredModel = self.baseModel.filter_new()
        attributes = [column[0] for column in columns]
        types = [column[1] for column in columns]
        self.filteredModel.set_modify_func(types, self.modify_func, attributes)

    def modify_func(self, model, iter_, column, attributes):
        childRowIter = self.filteredModel.convert_iter_to_child_iter(iter_)
        childModel = model.get_model()
        rowObject = childModel.get_object(childRowIter)
        return getattr(rowObject, attributes[column])

    def get_base_iter_(self, filteredRowIter):
        return self.filteredModel.convert_iter_to_child_iter(filteredRowIter)

    def get_object(self, filteredRowIter):
        return self.baseModel.get_object(self.get_base_iter_(filteredRowIter))

    def insert(self, rowObject):
        return self.baseModel.insert(rowObject)

    def update(self, newRowObject, filteredRowIter):
        return self.baseModel.update(newRowObject, self.get_base_iter_(filteredRowIter))

    def delete(self, filteredRowIter):
        return self.baseModel.delete(self.get_base_iter_(filteredRowIter))

    def clear(self):
        self.baseModel.clear()
