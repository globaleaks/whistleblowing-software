# -*- coding: UTF-8)
#
#   models/submission
#   *****************
#
# Storm DB table and ORM of the submisson temporary table

from storm.locals import Pickle, DateTime, Unicode, Reference
from storm.exceptions import NotOneError

from globaleaks.utils import idops, gltime
from globaleaks.models.base import TXModel
from globaleaks.models.externaltip import File
from globaleaks.models.receiver import Receiver
from globaleaks.models.context import Context
from globaleaks.rest.errors import ContextGusNotFound, SubmissionFailFields, SubmissionGusNotFound, \
    ReceiverGusNotFound, InvalidInputFormat, SubmissionConcluded, FileGusNotFound

from globaleaks.utils import log

__all__ = ['Submission']


class Submission(TXModel):

    def new(self, received_dict):

        self.files = []
        self.receivers = []
        self.mark = self._marker[0] # 'incomplete'

        self.creation_time = gltime.utcDateNow()
        # TODO with gltimes completed, just gltime.utcTimeNow(associated_c.submission_expire)
        self.expiration_time = gltime.utcFutureDate(seconds=1, minutes=1, hours=1)

        self.submission_gus = idops.random_submission_gus()

        try:
            self._import_dict(received_dict)
            self.context_gus = unicode(received_dict['context_gus'])

        except KeyError, e:
            raise InvalidInputFormat("Submission initialization failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("Submission initialization failed (wrong %s)" % e)

        try:
            associated_c = self.store.find(Context, Context.context_gus == self.context_gus).one()
        except NotOneError:
            raise ContextGusNotFound
        if associated_c is None:
            raise ContextGusNotFound

        self.context = associated_c

        self._receivers_check()
        self._files_check()

        if received_dict.has_key('finalize') and received_dict['finalize']:

            try:
                if not self._wb_fields_verify():
                    raise SubmissionFailFields
            except ValueError, e:
                print "[---] Unable to verify field: %s" % e
                raise SubmissionFailFields

            self.mark = self._marker[1] # 'finalized'

        self.store.add(self)
        return self._description_dict()


    def update(self, submission_gus, received_dict):

        try:
            s = self.store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
            s.store = self.store
        except NotOneError, e:
            raise SubmissionGusNotFound
        if not s:
            raise SubmissionGusNotFound

        if s.mark == self._marker[1]:
            # the session is finalized, you can't PUT
            raise SubmissionConcluded

        try:
            s._import_dict(received_dict)
        except KeyError, e:
            raise InvalidInputFormat("Submission update failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("Submission update failed (wrong %s)" % e)

        s._receivers_check()
        s._files_check()

        if received_dict['finalize']:

            try:
                if not s._wb_fields_verify():
                    raise SubmissionFailFields
            except ValueError, e:
                print "[---] Unable to verify field: %s" % e
                raise SubmissionFailFields

            s.mark = self._marker[1] # 'finalized'

        return s._description_dict()




    def _import_dict(self, received_dict):

        self.wb_fields = received_dict['wb_fields']
        self.receivers = received_dict['receivers']
        self.files = received_dict['files']


    def submission_delete(self, submission_gus, wb_request):

        try:
            requested_s = self.store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        if requested_s.mark == self._marker[1] and wb_request:
            # the session is finalized, you can't DELETE
            raise SubmissionConcluded

        self.store.remove(requested_s)


    def get_single(self, submission_gus):

        try:
            requested_s = self.store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        return requested_s._description_dict()


    def get_all(self):

        # I didn't understand why, but NotOneError is not raised even if the search return None
        present_s = self.store.find(Submission)

        subList = []
        for s in present_s:
            subList.append(s._description_dict())

        return subList


    def _description_dict(self):

        descriptionDict = {
            'submission_gus': unicode(self.submission_gus),
            'wb_fields' : dict(self.wb_fields) if self.wb_fields else {},
            'context_gus' : unicode(self.context_gus),
            'creation_time' : unicode(gltime.prettyDateTime(self.creation_time)),
            'expiration_time' : unicode(gltime.prettyDateTime(self.expiration_time)),
            'receivers' : list(self.receivers) if self.receivers else [],
            'files' : dict(self.files) if self.files else {},
            'finalize' : True if self.mark == self._marker[1] else False
        }

        return dict(descriptionDict)
