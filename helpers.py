import os
import datetime
import random

from google.appengine.api import memcache
from google.appengine.api import users

import logging
import functools


def cached(name, timeout=60):
    def wrapper(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            cachename = name+str(args)
            data = memcache.get(cachename)
            if not data:
                logging.info("CACHE MISS for "+cachename)
                data = method(self, *args, **kwargs)
                memcache.set(cachename, data, timeout)
            return data
        return wrapper
    return wrapper

def set_content_type(content_type):
    def wrapper(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            self.response.headers["Content-Type"] = content_type
            return method(self, *args, **kwargs)
        return wrapper
    return wrapper

def set_cache_age(age):
    def wrapper(method):
        @functools.wraps(method)
        def inner(*args, **kwargs):
            args[0].response.headers["Cache-Control"] = "max-age=%d" % (age)
            return method(*args, **kwargs)
        return inner
    return wrapper

def write_response(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.response.out.write(method(self, *args, **kwargs))
    return wrapper


def convert_keys(dictionary):
    d = {}
    for key in dictionary:
        value = dictionary[key]
        newkey = key.replace('-', '_')
        d[newkey] = value
        print "key: %s newkey: %s value-type: %s" % (key, newkey, type(value))
        if type(value) == type(dict()):
            d[newkey] = convert_keys(value)
    return d
        

