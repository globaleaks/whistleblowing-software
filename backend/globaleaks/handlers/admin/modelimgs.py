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


def db_get_model_img(store, obj_key, obj_id):
    model = model_map[obj_key]
    img =  store.find(model, model.id == obj_id).one()
    if img is None:
        return ''
    else:
        return img.data


@transact
def get_model_img(store, obj_key, obj_id):
    return db_get_model_img(store, obj_key, obj_id)


@transact
def add_model_img(store, obj_key, obj_id, data):
    model = model_map[obj_key]
    data = base64.b64encode(data)
    img = store.find(model, model.id == obj_id).one()
    if img is None:
        store.add(model({'id': obj_id, 'data': data}))
    else:
        img.data = data


@transact
def del_model_img(store, obj_key, obj_id):
    model = model_map[obj_key]
    store.find(model, model.id == obj_id).remove()


class ModelImgInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def post(self, obj_key, obj_id):
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            return

        # The error is suppressed here because add_model_img is wrapped with a
        # transact returns a deferred which we attach events to.
        # pylint: disable=assignment-from-no-return
        d = add_model_img(obj_key, obj_id, uploaded_file['body'].read())
        d.addBoth(lambda ignore: uploaded_file['body'].close)
        return d

    def delete(self, obj_key, obj_id):
        return del_model_img(obj_key, obj_id)
