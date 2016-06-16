# -*- coding: utf-8 -*-
#
# modelimgs
#  *****
#
# API handling upload/delete of users/contexts picture

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact, transact_ro
from globaleaks.rest.apicache import GLApiCache

model_map = {
  'users': models.User,
  'contexts': models.Context
}


def db_get_model_img(store, model, obj_id):
    picture = store.find(model, model.id == obj_id).one().picture
    return picture.data if picture is not None else ''


@transact_ro
def get_model_img(store, model, obj_id):
    return db_get_model_img(store, model, obj_id)


@transact
def add_model_img(store, model, obj_id, data):
    obj = store.find(model, model.id == obj_id).one()
    if obj:
        if obj.picture is None:
            obj.picture = models.File()

        obj.picture.data = data


@transact
def del_model_img(store, model, obj_id):
    obj = store.find(model, model.id == obj_id).one()
    if obj is not None and obj.picture is not None:
        store.remove(obj.picture)


class ModelImgInstance(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self, obj_key, obj_id):
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            self.set_status(201)
            return

        try:
            yield add_model_img(model_map[obj_key], obj_id, uploaded_file['body'].read())
        except:
            pass
        finally:
            uploaded_file['body'].close()

        GLApiCache.invalidate()

        self.set_status(201)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self, obj_key, obj_id):
        yield del_model_img(model_map[obj_key], obj_id)

        GLApiCache.invalidate()
