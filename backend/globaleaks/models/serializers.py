# -*- coding: utf-8
from globaleaks import models


def serialize_ifile(session, ifile):
    """
    Transaction for serializing ifiles

    :param session: An ORM session
    :param ifile: The ifile to be serialized
    :return: The serialized ifile
    """
    return {
        'id': ifile.id,
        'creation_date': ifile.creation_date,
        'name': ifile.name,
        'size': ifile.size,
        'type': ifile.content_type
    }


def serialize_rfile(session, rfile):
    """
    Transaction for serializing rfile

    :param session: An ORM session
    :param rfile: The rfile to be serialized
    :return: The serialized rfile
    """
    ifile = session.query(models.InternalFile) \
                   .filter(models.InternalFile.id == models.ReceiverFile.internalfile_id,
                           models.ReceiverFile.id == rfile.id).one()

    return {
        'id': rfile.id,
        'creation_date': ifile.creation_date,
        'name': ifile.name,
        'size': ifile.size,
        'type': ifile.content_type,
        'filename': rfile.filename,
        'downloads': rfile.downloads,
        'status': rfile.status
    }


def serialize_wbfile(session, wbfile):
    """
    Transaction for serializing wbfile

    :param session: An ORM session
    :param wbfile: The wbfile to be serialized
    :return: The serialized wbfile
    """
    receiver_id = session.query(models.ReceiverTip.receiver_id) \
                         .filter(models.ReceiverTip.id == wbfile.receivertip_id).one()

    return {
        'id': wbfile.id,
        'creation_date': wbfile.creation_date,
        'name': wbfile.name,
        'size': wbfile.size,
        'type': wbfile.content_type,
        'filename': wbfile.filename,
        'description': wbfile.description,
        'downloads': wbfile.downloads,
        'author': receiver_id
    }


def serialize_redirect(redirect):
    """
    Transact for serializing a redirect

    :param redirect: The redirect to be serialized
    :return: The serialized redirect
    """
    return {
        'id': redirect.id,
        'path1': redirect.path1,
        'path2': redirect.path2
    }
