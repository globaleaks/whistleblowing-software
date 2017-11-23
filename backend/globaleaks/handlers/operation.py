# -*- coding: utf-8 -*-
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors, requests


class OperationHandler(BaseHandler):
    def operation_descriptors(self):
        raise NotImplementedError

    def put(self, *args, **kwargs):
        request = self.validate_message(self.request.content.read(), requests.OpsDesc)

        op_desc = self.operation_descriptors().get(request['operation'], None)
        if op_desc is None:
            raise errors.InvalidInputFormat('Invalid command')

        func, obj_validator = op_desc
        if obj_validator is not None:
            self.validate_jmessage(request['args'], obj_validator)

        return func(self, request['args'], *args, **kwargs)
