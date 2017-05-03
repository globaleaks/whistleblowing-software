# -*- coding: UTF-8
#
# overview
#   ********
# Implementation of the code executed when an HTTP client reach /overview/* URI

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.utils.structures import Rosetta
from globaleaks.utils.utility import datetime_to_ISO8601


@transact
def collect_tip_overview(store, language):
    tip_description_list = []

    all_itips = store.find(models.InternalTip)
    for itip in all_itips:
        tip_description = {
            'id': itip.id,
            'creation_date': datetime_to_ISO8601(itip.creation_date),
            'expiration_date': datetime_to_ISO8601(itip.expiration_date),
            'context_id': itip.context_id
        }

        mo = Rosetta(itip.context.localized_keys)
        mo.acquire_storm_object(itip.context)
        tip_description['context_name'] = mo.dump_localized_key('name', language)

        tip_description_list.append(tip_description)

    return tip_description_list


@transact
def collect_files_overview(store):
    file_description_list = []

    for ifile in store.find(models.InternalFile):
        file_desc = {
            'id': ifile.id,
            'itip': ifile.internaltip_id,
            'path': ifile.file_path,
            'size': ifile.size
        }

        file_description_list.append(file_desc)

    for rfile in store.find(models.ReceiverFile):
        file_desc = {
            'id': rfile.internalfile_id,
            'itip': rfile.internalfile.internaltip_id,
            'path': rfile.file_path,
            'size': rfile.size

        }

        file_description_list.append(file_desc)

    return file_description_list


class Tips(BaseHandler):
    """
    /admin/overview/tips
    Dump the list of the active tips with various information
    """
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: TipsOverviewDescList
        Errors: None
        """
        tips_complete_list = yield collect_tip_overview(self.request.language)

        self.write(tips_complete_list)


class Files(BaseHandler):
    """
    /admin/overview/files

    Return the list of the files in InternalFile, ReceiverFile
    and the files in
    """
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: FilesOverviewDescList
        Errors: None
        """
        file_complete_list = yield collect_files_overview()

        self.write(file_complete_list)
