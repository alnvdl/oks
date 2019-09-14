#!/usr/bin/env python
#-*- coding:utf-8 -*-


from gi.repository import Gtk as gtk


class AutoCompletion:
    def __init__(self):
        self.completions = {}

    def register(self, name, model, col,
                 filter_col = None, filter_value = None, inline = False):
        self.completions[name] = (model, col, filter_col, filter_value, inline)

    def get(self, name):
        model, col, filter_col, filter_value, inline = self.completions[name]

        if filter_col and filter_value:
            def match_func(completion, key, iter_):
                return (key.lower() in model[iter_][col].lower() and
                        model[iter_][filter_col] == filter_value)
        else:
            def match_func(completion, key, iter_):
                return key.lower() in model[iter_][col].lower()

        completion = gtk.EntryCompletion()
        completion.set_model(model)
        completion.set_match_func(match_func)
        completion.set_text_column(col)

        if inline:
            completion.set_popup_completion(False)
            completion.set_inline_completion(True)
        else:
            completion.set_inline_selection(True)
            completion.set_popup_set_width(True)

        return completion
