# -*- coding: UTF-8)
#
#   models/submission
#   *****************
#
# Storm DB table and ORM of the submisson temporary table

from storm.twisted.transact import transact
from storm.locals import Int, Pickle, DateTime, Unicode, Reference
from storm.exceptions import NotOneError

from globaleaks.utils import idops, gltime, random
from globaleaks.models.base import TXModel
from globaleaks.models.externaltip import File
from globaleaks.models.receiver import Receiver
from globaleaks.models.context import Context
from globaleaks.rest.errors import ContextGusNotFound, SubmissionFailFields, SubmissionGusNotFound, \
    ReceiverGusNotFound, InvalidInputFormat, SubmissionConcluded, FileGusNotFound

from globaleaks.utils import log

__all__ = ['Submission']


class Submission(TXModel):
    """
    This represents a temporary submission. Submissions should be stored here
    until they are transformed into a Tip.
    """

    __storm_table__ = 'submissions'

    submission_gus = Unicode(primary=True)

    wb_fields = Pickle()
    creation_time = DateTime()
    expiration_time = DateTime()

    mark = Unicode()
    receivers = Pickle()
    files = Pickle()

    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)

    _marker = [ u'incomplete', u'finalized' ]


    @transact
    def new(self, received_dict):

        store = self.getStore()

        self.files = []
        self.receivers = []
        self.mark = self._marker[0] # 'incomplete'

        self.creation_time = gltime.utcDateNow()
        # TODO with gltimes completed, just gltime.utcTimeNow(associated_c.submission_expire)
        self.expiration_time = gltime.utcFutureDate(seconds=1, minutes=1, hours=1)

        try:
            self._import_dict(received_dict)
        except KeyError, e:
            raise InvalidInputFormat("Submission initialization failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("Submission initialization failed (wrong %s)" % e)

        try:
            associated_c = store.find(Context, Context.context_gus == unicode(self.context_gus)).one()
        except NotOneError:
            raise ContextGusNotFound
        if associated_c is None:
            raise ContextGusNotFound

        self.context = associated_c

        """
        try:
            if not self._wb_fields_verify():
                raise SubmissionFailFields
        except ValueError, e:
            print "[---] Unable to verify field: %s" % e
            raise SubmissionFailFields
        """
        # XXX remind talk with Arturo about this. I don't want invalid field also in not completed submission
        # but client want open a submission before having sent them

        # TODO those file/receiver checks can be reduced in one function after the refactor #46

        for single_r in self.receivers:
            try:
                selected_r = store.find(Receiver, Receiver.receiver_gus == unicode(single_r)).one()
            except NotOneError:
                raise ReceiverGusNotFound
            if selected_r is None:
                raise ReceiverGusNotFound
            if not self.context_gus in selected_r.contexts:
                print "[***] Invalid Receiver relationship:", s.context_gus, selected_r.contexts
                raise ReceiverGusNotFound

        for single_f in self.files:
            try:
                selected_f = store.find(File, File.file_gus == unicode(single_f)).one()
            except NotOneError:
                raise FileGusNotFound
            if selected_f is None:
                raise FileGusNotFound

        self.submission_gus = idops.random_submission_gus()

        if received_dict.has_key('finalize') and received_dict['finalize']:
            print "INFO, Finalized in new", self.submission_gus
            self.mark = self._marker[1] # 'finalized'
        else:
            print "INFO, NOT finalized in new", self.submission_gus

        store.add(self)
        return self._description_dict()


    @transact
    def update(self, submission_gus, received_dict):

        store = self.getStore()

        try:
            s = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
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

        try:
            if not s._wb_fields_verify():
                raise SubmissionFailFields
        except ValueError, e:
            # XXX this would be a log or an error for the client ?
            print "[---] Unable to verify field: %s" % e
            raise SubmissionFailFields

        # TODO those file/receiver checks can be reduced in one function after the refactor #46

        for single_r in s.receivers:
            try:
                selected_r = store.find(Receiver, Receiver.receiver_gus == unicode(single_r)).one()
            except NotOneError:
                raise ReceiverGusNotFound
            if selected_r is None:
                raise ReceiverGusNotFound
            if not s.context_gus in selected_r.contexts:
                # XXX this would be a log or an error for the client ?
                print "[***] Invalid Receiver relationship:", s.context_gus, selected_r.contexts
                raise ReceiverGusNotFound

        for single_f in s.files:
            try:
                selected_f = store.find(File, File.file_gus == unicode(single_f)).one()
            except NotOneError:
                raise FileGusNotFound
            if selected_f is None:
                raise FileGusNotFound

        if received_dict['finalize']:
            s.mark = self._marker[1] # 'finalized'

        return s._description_dict()


    # not a transact, called by new/update
    def _wb_fields_verify(self):
        """
        @return: False is verifications fail.
            Perform two kind of verification: if the required fields
            are present, and if
        """
        for entry in self.context.fields:
            if entry['required']:
                if not self.wb_fields.has_key(entry['name']):
                    # XXX this would be a log or an error for the client ?
                    print "[---] missing field '%s': Required" % entry['name']
                    return False

        for k, v in self.wb_fields.iteritems():
            key_exists = False

            for entry in self.context.fields:
                if k == entry['name']:
                    key_exists = True
                    break

            if not key_exists:
                # XXX this would be a log or an error for the client ?
                print "[---] Submitted field '%s' not expected in context" % k
                return False

        return True


    # not a transact, called by new/update
    def _import_dict(self, received_dict):

        # context can't be changed in update
        if self.context_gus and unicode(received_dict['context_gus']) != self.context_gus:
            raise InvalidInputFormat("Context change is not permitted")

        self.context_gus = received_dict['context_gus']
        self.receivers = received_dict['receivers']
        self.wb_fields = received_dict['wb_fields']
        self.files = received_dict['files']


    @transact
    def submission_delete(self, submission_gus):

        store = self.getStore()

        try:
            requested_s = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        if requested_s.mark == self._marker[1]:
            # the session is finalized, you can't DELETE
            raise SubmissionConcluded

        store.remove(requested_s)


    @transact
    def get_single(self, submission_gus):

        store = self.getStore()

        try:
            requested_s = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        return requested_s._description_dict()

    @transact
    def get_all(self):

        store = self.getStore()

        # I didn't understand why, but NotOneError is not raised even if the search return None
        present_s = store.find(Submission)

        subList = []
        for s in present_s:
            subList.append(s._description_dict())

        return subList


    # called by a transact method, return
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
