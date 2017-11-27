# -*- coding: utf-8 -*-
#
# modelimgs
#  *****
#
# API handling upload/delete of users/contexts picture
import base64

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact

model_map = {
  'users': models.UserImg,
  'contexts': models.ContextImg
}


def db_get_model_img(store, tid, obj_key, obj_id):
    model = model_map[obj_key]
    img =  store.find(model, model.id == obj_id, tid=tid).one()
    if img is None:
        return ''
    else:
        return img.data


@transact
def get_model_img(store, tid, obj_key, obj_id):
    return db_get_model_img(store, tid, obj_key, obj_id)


@transact
def add_model_img(store, tid, obj_key, obj_id, data):
    model = model_map[obj_key]
    data = base64.b64encode(data)
    img = store.find(model, model.id == obj_id, tid=tid).one()
    if img is None:
        store.add(model({'tid': tid, 'id': obj_id, 'data': data}))
    else:
        img.data = data


@transact
def del_model_img(store, tid, obj_key, obj_id):
    model = model_map[obj_key]
    store.find(model, model.id == obj_id, tid=tid).remove()


class ModelImgInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True
    upload_handler = True

    def post(self, obj_key, obj_id):
        # The error is suppressed here because add_model_img is wrapped with a
        # transact returns a deferred which we attach events to.
        # pylint: disable=assignment-from-no-return
        return add_model_img(self.request.tid, obj_key, obj_id, self.uploaded_file['body'].read())

    def delete(self, obj_key, obj_id):
        return del_model_img(self.request.tid, obj_key, obj_id)
