from globaleaks.utils.utility import datetime_to_ISO8601


# InternaltFile
def serialize_ifile(ifile):
    return {
        'id': ifile.id,
        'creation_date': datetime_to_ISO8601(ifile.creation_date),
        'name': ifile.name,
        'size': ifile.size,
        'content_type': ifile.content_type
    }


# ReceiverFile
def serialize_rfile(rfile):
    ifile = rfile.internalfile

    return {
        'id': rfile.id,
        'creation_date': datetime_to_ISO8601(ifile.creation_date),
        'name': ("%s.pgp" % ifile.name) if rfile.status == u'encrypted' else ifile.name,
        'size': rfile.size,
        'content_type': ifile.content_type,
        'path': rfile.file_path,
        'downloads': rfile.downloads
    }
