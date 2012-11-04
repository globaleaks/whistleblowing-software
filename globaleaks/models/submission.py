# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from twisted.internet.defer import returnValue, inlineCallbacks
from storm.twisted.transact import transact
from storm.locals import Int, Pickle, Date, Unicode, Reference
from storm.exceptions import NotOneError, NoneError

from globaleaks.utils import idops, gltime
from globaleaks.models.base import TXModel, ModelError
from globaleaks.models.tip import InternalTip, Tip, ReceiverTip, File, Folder
from globaleaks.models.context import Context

from globaleaks.utils import log

__all__ = ['Submission']

class SubmissionNotFoundError(ModelError):

    def __init__(self):
        ModelError.error_message = "Invalid Submission addressed with submission_gus"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 400 # Bad Request

# may it exists ? I've used that for wrap eventually "database is locked", but
# we've see that database locked is an effect of a programmer bug, not a
# common behavior, also in multiple requests
class SubmissionGenericError(ModelError):

    def __init__(self):
        ModelError.error_message = " Submission internal error: sorry!"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 500 # Server Error


# TODO - remove this possibility
class SubmissionNoContextSelectedError(ModelError):

    def __init__(self):
        ModelError.error_message = "Invalid context selected"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 412 # Precondition Failed

# TODO - remove this possibility, too
class SubmissionContextNotFoundError(ModelError):
    pass

# implausible - is controlled by Admin the amount of Contexts
class SubmissionContextNotOneError(ModelError):
    pass

# TODO - would be an error when we start to check presence of required fields
class SubmissionFailRequiremers(ModelError):
    pass

class Submission(TXModel):
    """
    This represents a temporary submission. Submissions should be stored here
    until they are transformed into a Tip.
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class Submission")
    __storm_table__ = 'submission'

    submission_gus = Unicode(primary=True)
    context_selected = Unicode()

    fields = Pickle()


    folder_gus = Unicode()
    folder = Reference(folder_gus, Folder.folder_gus)
    mark = Unicode()
        # TODO ENUM: 'incomplete' 'finalized'

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)

    creation_time = Date()

    @transact
    def new(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "new")
        store = self.getStore('new')

        submission_gus = idops.random_submission_gus(False)
        creation_time = gltime.utcDateNow()

        submission = Submission()
        submission.submission_gus = submission_gus
        submission.creation_time = creation_time
        mark = u'incomplete'

        folder = Folder()
        folder.folder_gus = idops.random_folder_gus()
        store.add(folder)

        submission.folder = folder
        store.add(submission)

        response = {
            "submission_gus": submission_gus,
            "creation_time": gltime.dateToTime(creation_time),
            "folder_gus": folder.folder_gus
        }

        store.commit()
        store.close()

        return response

    @transact
    def add_file(self, submission_gus, file_name=None):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "add_file", "submission_gus", submission_gus , "file_name", file_name )
        store = self.getStore('add_file')
        submission = store.find(Submission, Submission.submission_gus==submission_gus).one()

        if not submission:
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        new_file_gus = idops.random_file_gus()
        log.debug("Generated this file id %s" % new_file_gus)
        new_file = File()

        new_file.folder_gus = submission.folder_gus
        new_file.file_gus = unicode(new_file_gus)
        store.add(new_file)

        try:
            store.commit()
        except Exception, e:
            log.exception("[E]: %s %s " % (__file__, __name__), "Submission", "add_file", "submission_gus", submission_gus, "file_name", file_name )
            store.rollback()
            store.close()
            raise SubmissionGenericError

        log.debug("Added file %s to %s" % (submission_gus, file_name))
        store.close()
        return new_file_gus

    @transact
    def update_fields(self, submission_gus, fields):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "update_fields", "submission_gus", submission_gus, "fields", fields )

        store = self.getStore('update_fields')
        try:
            s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError, e:
            # XXX these log lines will be removed in the near future
            log.err("[E] update_fields: Problem looking up %s" % submission_gus)
            log.err(e)
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        if not s:
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        if not s.fields:
            s.fields = {}

        for k, v in fields.items():
            s.fields[k] = v

        try:
            store.commit()
        except Exception, e:
            log.exception("[E]: %s %s " % (__file__, __name__), "Submission", "update_fields", "submission_gus", submission_gus, "fields", fields )
            store.rollback()
            store.close()
            raise SubmissionGenericError

        store.close()

    # TODO - context need to be selected when submission_gus is received, is not to be declared via
    # parameter, because different context may have different expiring time. and then, in the
    # asynchronous cleaning procedure, may exists a submission without context and then without
    # expiring time. This would be avoided making the context declared when submission_gus is
    # received. in client side, the fields of every context is already know, then this is not
    # a blocking operation.
    #
    # when this patch in API - handlers - client, happen, this function would be removed.
    @transact
    def select_context(self, submission_gus, context_gus):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "select_context", "submission_gus", submission_gus, "context", context_gus )

        store = self.getStore('select_context')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            # its not possible: is a primary key
            store.close()
            raise SubmissionNotFoundError
        if requested_s is None:
            store.close()
            raise SubmissionNotFoundError

        requested_s.context_selected = context_gus

        try:
            store.commit()
        except Exception, e:
            log.debug("[E]: %s %s " % (__file__, __name__), "Submission", "select_context", "submission_gus", submission_gus, "context", context_gus )
            store.rollback()
            store.close()
            raise SubmissionGenericError

        store.close()

    @transact
    def select_receiver(self, submission_gus, receiver_id_list):
        pass

    @transact
    def status(self, submission_gus):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "status", "submission_gus", submission_gus )

        store = self.getStore('status')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            # its not possible: is a primary key
            store.close()
            raise SubmissionNotFoundError
        if requested_s is None:
            store.close()
            raise SubmissionNotFoundError

        statusDict = {'context_selected': requested_s.context_selected,
                      'fields': requested_s.fields}
                # TODO 'creation_time' and 'expiration_time'
                # would be done when date format is clear

        store.close()
        return statusDict

    @transact
    def complete_submission(self, submission_gus, proposed_receipt):
        """
        this function is became simply unmaintainable
        """
        log.debug("[D] ",__file__, __name__, "Submission complete_submission", submission_gus, "proposed_receipt", proposed_receipt)

        store = self.getStore('complete_submission')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            store.close()
            raise SubmissionNotFoundError
        if requested_s is None:
            store.close()
            raise SubmissionNotFoundError

        if not requested_s.context_selected:
            store.close()
            raise SubmissionNoContextSelectedError

        try:
            requested_c = store.find(Context,
                    Context.context_gus == requested_s.context_selected).one()
        except NotOneError:
            store.close()
            raise SubmissionContextNotOneError
        if not requested_c:
            store.close()
            raise SubmissionContextNotFoundError

        log.debug("Creating internal tip", requested_c.context_gus, requested_s.submission_gus)

        try:
            internal_tip = InternalTip()
            internal_tip.fields = requested_s.fields
            internal_tip.context_gus = requested_s.context_selected
            store.add(internal_tip)
        except Exception, e:
            log.err(e)
            store.rollback()
            store.close()
            raise SubmissionGenericError

        log.debug("Created internal tip %s" % internal_tip.context_gus)

        # this is wrong, we need to check if some file has been added TODO
        # temporary fail in this check, folder would be associated in internaltip, but
        # marked coherently with the asynchronous delivery logic
        if requested_s.folder and 1 == 0:
            log.debug("Creating submission folder table %s" % requested_s.folder_gus)
            folder = requested_s.folder
            folder.internaltip = internal_tip

            store.add(folder) 
            store.commit()

            log.debug("Submission folder created without error")

            # XXX, and I don't get why folder_gus is returned by new():
            # because file uploader # use submission_gus as reference, do not need folder_gus too.
            # because if someone want restore an upload, use the file_gus instead of folder_gus

        log.debug("Creating tip for whistleblower")
        whistleblower_tip = Tip()
        whistleblower_tip.internaltip = internal_tip

        # if context permit that receiver propose the receipt:
        whistleblower_tip.address = proposed_receipt
        # because is already an hashed receipt
        # else... receipt_string = idops.random_receipt_id()
        #         hash(receipt_string)
        #         return receipt_string
        # AND, check if not other equal receipt are present, in that case, reject
        # XXX this should bring security issue... mmmhh....


        store.add(whistleblower_tip)
        log.debug("Created tip with address %s" % whistleblower_tip.address)


        log.debug("Submision is not removed now, because need to be processed by tip_creation async. Instead, has now internaltip linked")
        requested_s.mark = u'finalized'
        requested_s.internaltip = internal_tip

        store.commit()
        store.close()

        log.debug("create_internaltip and whistleblower tip")

        return proposed_receipt

    @transact
    def get_submissions(self, mark):
        """
        @param mark: one of them:
        # TODO ENUM: 'incomplete' 'finalized'
        @return: an array, emptry or with one or more dict.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Submission", "get_submissions", mark)

        retVal = []
        store = self.getStore('submission - get_submissions')

        try:
            searched_s = store.find(Submission, Submission.mark == mark)
        except:
            log.debug("get_submissions with mark %s goes in unknow exception !?" % mark)
            store.close()
            return retVal

        for single_s in searched_s:
            retVal.append(single_s._description_dict())

        store.close()
        return retVal


    @transact
    def admin_get_single(self, submission_gus):
        """
        @return a receiverDescriptionDict
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Submission", "admin_get_single", submission_gus)

        store = self.getStore('submission - admin_get_single')

        # I didn't understand why, but NotOneError is not raised even if the search return None
        try:
            requested_s = store.find(Submission, Submission.submission_gus == submission_gus).one()
        except NotOneError:
            store.close()
            raise SubmissionNotFoundError
        if requested_s is None:
            store.close()
            raise SubmissionNotFoundError

        retSubmission = requested_s._description_dict()

        store.close()
        return retSubmission

    @transact
    def admin_get_all(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Submission", "admin_get_all")
        pass


    def _description_dict(self):

        descriptionDict = {
            'submission_gus': self.submission_gus,
            'fields' : self.fields,
            'context_selected' : self.context_selected,
            'mark' : self.mark,
            # folder and internaltip would be reported as sub-dict only if present
            'folder_gus' : self.folder_gus,
            'internaltip_id' : self.internaltip_id
        }

        return descriptionDict
