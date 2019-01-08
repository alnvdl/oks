#!/usr/bin/env python
#-*- coding:utf-8 -*-

import datetime
import locale

# Caching function
def cache(function):
    """ Simple decorator that caches by relating the arguments for a function 
    to its return value """
    cache = {}
    
    def decorating_function(*args, **kwargs):
        cache_ = cache
        function_ = function
        key = str((args, kwargs))
        
        try:
            return cache_[key]
        except KeyError:
            cache_[key] = function_(*args, **kwargs)
            return cache_[key]
        
    decorating_function.cache = cache
    decorating_function.__doc__ = function.__doc__
    decorating_function.__name__ = function.__name__
    return decorating_function
    
    
def date_to_str(date, fmt=locale.nl_langinfo(locale.D_FMT)):
    return date.strftime(fmt)


decimal_point = locale.localeconv()["decimal_point"]
def float_to_str(n, digits = 2, strip = False):
    value = locale.format("%.{0}f".format(digits), n)
    if strip:
        return value.rstrip("0"*digits).rstrip(decimal_point)
    return value
    
    
str_to_float = locale.atof

def float_to_currency(value, unit=False):
    return locale.currency(value, unit)
    
    
def internal_date_to_str(date, ifmt, fmt=locale.nl_langinfo(locale.D_FMT)):
    date = datetime.datetime.strptime(date, ifmt)
    return date_to_str(datetime.date(date.year, date.month, date.day), fmt)
