# -*- coding: utf-8 -*-
import base64

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact

model_map = {
    'users': models.UserImg,
    'contexts': models.ContextImg
}


def db_get_model_img(session, obj_type, obj_id):
    """
    Transaction for retrieving the image associated to a model type

    :param session: An ORM session
    :param obj_type: The model type
    :param obj_id: The object ID
    :return: The image for the specified object
    """
    model = model_map[obj_type]
    img = session.query(model).filter(model.id == obj_id).one_or_none()
    return img.data if img is not None else ''


@transact
def add_model_img(session, obj_key, obj_id, data):
    model = model_map[obj_key]
    data = base64.b64encode(data).decode()
    img = session.query(model).filter(model.id == obj_id).one_or_none()
    if img is None:
        session.add(model({'id': obj_id, 'data': data}))
    else:
        img.data = data


@transact
def del_model_img(session, obj_key, obj_id):
    model = model_map[obj_key]
    session.query(model).filter(model.id == obj_id).delete(synchronize_session='fetch')


class ModelImgInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True
    upload_handler = True

    def post(self, obj_key, obj_id):
        sf = self.state.get_tmp_file_by_name(self.uploaded_file['filename'])
        with sf.open('r') as encrypted_file:
            data = encrypted_file.read()

        return add_model_img(obj_key, obj_id, data)

    def delete(self, obj_key, obj_id):
        return del_model_img(obj_key, obj_id)
