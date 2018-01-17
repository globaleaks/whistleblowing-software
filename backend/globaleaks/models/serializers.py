# -*- coding: utf-8

from globaleaks import models
from globaleaks.utils.utility import datetime_to_ISO8601


# InternaltFile
def serialize_ifile(session, ifile):
    return {
        'id': ifile.id,
        'creation_date': datetime_to_ISO8601(ifile.creation_date),
        'name': ifile.name,
        'size': ifile.size,
        'content_type': ifile.content_type
    }


# ReceiverFile
def serialize_rfile(session, tid, rfile):
    ifile = session.query(models.InternalFile) \
                 .filter(models.InternalFile.id == models.ReceiverFile.internalfile_id,
                         models.ReceiverFile.id == rfile.id,
                         models.InternalFile.tid == tid).one()

    return {
        'id': rfile.id,
        'creation_date': datetime_to_ISO8601(ifile.creation_date),
        'name': ("%s.pgp" % ifile.name) if rfile.status == u'encrypted' else ifile.name,
        'size': rfile.size,
        'content_type': ifile.content_type,
        'path': rfile.file_path,
        'downloads': rfile.downloads,
        'status': rfile.status
    }

# WhistleblowerFile
def serialize_wbfile(session, tid, wbfile):
    receiver_id = session.query(models.ReceiverTip.receiver_id) \
                       .filter(models.ReceiverTip.id == wbfile.receivertip_id,
                               models.ReceiverTip.tid == tid).one()

    return {
        'id': wbfile.id,
        'creation_date': datetime_to_ISO8601(wbfile.creation_date),
        'name': wbfile.name,
        'size': wbfile.size,
        'content_type': wbfile.content_type,
        'path': wbfile.file_path,
        'downloads': wbfile.downloads,
        'author': receiver_id,
    }
