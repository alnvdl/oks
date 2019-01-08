#!/usr/bin/env python
#-*- coding:utf-8 -*-


from core.output import *
from core.output.handlers.string import StringOutputHandler


class ViewOutputHandler(StringOutputHandler):
    def __init__(self):
        StringOutputHandler.__init__(self)
    
    def output(self, outputable):
        if isinstance(outputable, Section):
            title = outputable.title
            outputable.title = None
            content = StringOutputHandler.output(self, outputable)
            outputable.title = title
            return (title, content)
        return ("", "")
