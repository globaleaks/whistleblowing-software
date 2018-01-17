# -*- coding: utf-8
#
# overview
#   ********
# Implementation of the code executed when an HTTP client reach /overview/* URI
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.utils.utility import datetime_to_ISO8601


@transact
def collect_tip_overview(session, tid, language):
    tip_description_list = []

    for itip in session.query(models.InternalTip).filter(models.InternalTip.tid == tid):
        tip_description_list.append({
            'id': itip.id,
            'creation_date': datetime_to_ISO8601(itip.creation_date),
            'expiration_date': datetime_to_ISO8601(itip.expiration_date),
            'context_id': itip.context_id
        })

    return tip_description_list


@transact
def collect_files_overview(session, tid):
    file_description_list = []

    for ifile in session.query(models.InternalFile).filter(models.InternalFile.tid == tid):
        file_description_list.append({
            'id': ifile.id,
            'itip': ifile.internaltip_id,
            'path': ifile.file_path,
            'size': ifile.size
        })

    for rfile, itip in session.query(models.ReceiverFile, models.InternalFile) \
                            .filter(models.ReceiverFile.internalfile_id == models.InternalFile.id,
                                    models.InternalFile.tid == tid):
        file_description_list.append({
            'id': rfile.internalfile_id,
            'itip': itip.id,
            'path': rfile.file_path,
            'size': rfile.size

        })

    return file_description_list


class Tips(BaseHandler):
    """
    /admin/overview/tips
    Dump the list of the active tips with various information
    """
    check_roles = 'admin'

    def get(self):
        """
        Parameters: None
        Response: TipsOverviewDescList
        Errors: None
        """
        return collect_tip_overview(self.request.tid, self.request.language)


class Files(BaseHandler):
    """
    /admin/overview/files

    Return the list of the files in InternalFile, ReceiverFile
    and the files in
    """
    check_roles = 'admin'

    def get(self):
        """
        Parameters: None
        Response: FilesOverviewDescList
        Errors: None
        """
        return collect_files_overview(self.request.tid)
