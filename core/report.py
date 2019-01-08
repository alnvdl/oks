#!/usr/bin/env python
#-*- coding:utf-8 -*-

import datetime

from core.output import *

class Report:
    NAME = ""
    DESCRIPTION = ""
    OPTIONS = []
    
    def __init__(self, db):
        self.db = db
        self.data = []
        self.bits = []
        
        # An option has the following syntax:
        # (name, type_, label, value)
        # 
        # name is an ID for the option
        # type_ is the option type
        # label is the label shown to the user
        # value is the default value for the option
        for (name, type_, label, value) in self.OPTIONS:
            self.set_option(name, value)
            
    def register_option(self, option, type_, label, value):
        self.OPTIONS.append((option, type_, label, value))
        self.set_option(option, value)
        
    def get_option(self, option):
        return getattr(self, option)
        
    def set_option(self, option, value):
        setattr(self, option, value)
        
    def make(self):
        self.data = []
        self.bits = []
    
    def make_output(self):
        self.make()
