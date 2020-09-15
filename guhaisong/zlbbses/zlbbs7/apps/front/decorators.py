#encoding: utf-8
from functools import wraps
from flask import session,redirect,url_for
import config

def login_required(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if config.FRONT_USER_ID in session:
            return func(*args,**kwargs)
        else:
            return redirect(url_for('front.signin'))
    return inner