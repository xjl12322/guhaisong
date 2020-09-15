#encoding: utf-8

from wtforms import Form


class BaseForm(Form):
    def get_error(self):
        message = self.errors.popitem()[1][0]
        return message