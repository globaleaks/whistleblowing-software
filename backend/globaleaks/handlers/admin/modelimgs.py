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
  'users': models.User,
  'contexts': models.Context
}


def db_get_model_img(store, model, obj_id):
    obj = store.find(model, model.id == obj_id).one()
    if obj.img_id is None:
        return ''

    return store.find(models.File, models.File.id == obj.img_id).one().data


@transact
def get_model_img(store, model, obj_id):
    return db_get_model_img(store, model, obj_id)


@transact
def add_model_img(store, model, obj_id, data):
    data = base64.b64encode(data)
    obj = store.find(model, model.id == obj_id).one()
    if obj.img_id is not None:
        picture = store.find(models.File, models.File.id == obj.img_id).one()
    else:
        picture = models.File({'data': data})
        store.add(picture)
        obj.img_id = picture.id

    picture.data = data


@transact
def del_model_img(store, model, obj_id):
    obj = store.find(model, model.id == obj_id).one()
    if obj.img_id != '':
        store.find(models.File, models.File.id == obj.img_id).remove()


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
        d = add_model_img(model_map[obj_key], obj_id, uploaded_file['body'].read())
        d.addBoth(lambda ignore: uploaded_file['body'].close)
        return d

    def delete(self, obj_key, obj_id):
        return del_model_img(model_map[obj_key], obj_id)
