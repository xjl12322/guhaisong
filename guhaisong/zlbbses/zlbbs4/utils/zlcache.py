#encoding: utf-8

import memcache

cache = memcache.Client(['127.0.0.1:11211'],debug=True)

def set(key,value,timeout=60):
    return cache.set(key,value,timeout)

def get(key):
    return cache.get(key)

def delete(key):
    return cache.delete(key)