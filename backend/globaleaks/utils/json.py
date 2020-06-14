# -*- coding: utf-8
import datetime
import json

from globaleaks.utils.utility import datetime_to_ISO8601


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return datetime_to_ISO8601(obj)
        else:
            return super().default(obj)
