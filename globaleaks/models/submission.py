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
from globaleaks.models.admin import Context

from globaleaks.jobs.delivery import Delivery
from globaleaks.jobs.notification import Notification

from globaleaks.scheduler.manager import work_manager
from globaleaks.utils import log

__all__ = ['Submission']

"""
This ORM implementation is called whistleblower, because contain the information mostly useful
for the WBs, other elements used by WBs stay on globaleaks.db.tips.SpecialTip
"""

def safeGetStorage(targetObj, info=''):
    from time import sleep
    import sqlite3

    delaytime = 0.01
    safe_but_not_deadlock = 0
    store = None

    while(1):

        if safe_but_not_deadlock > 3:
            raise Exception("Storm Hell")

        try:
            store = targetObj.getStore()
            log.debug("[W] completed getStore successfully %s" % info)
            break
        except sqlite3.OperationalError:
            safe_but_not_deadlock += 1
            log.debug("[W] getStore/ db locked, but %f sleep and check again %d %s" % ( delaytime, safe_but_not_deadlock, info) )
            sleep(delaytime)
            continue

    return store

def safeCommit(targetStore, info=''):
    from time import sleep
    import sqlite3

    delaytime = 0.01
    """
    for same TwistedStorm reason, putting a sleep of 0.01 cause a sleep of 2 second.
    causing a 2 second sleep, cause a block of 4 seconds, and so on.
    """
    safe_but_not_deadlock = 0

    while(1):

        if safe_but_not_deadlock > 3:
            raise Exception("Storm Hell")

        try:
            targetStore.commit()
            log.debug("[W] completed commit successfully %s" % info)
            break
        except sqlite3.OperationalError:
            safe_but_not_deadlock += 1
            log.debug("[W] commit/ db locked, but %f sleep and check again %d %s" % ( delaytime, safe_but_not_deadlock, info) )
            sleep(delaytime)
            continue

class SubmissionModelError(ModelError):
    pass

class SubmissionNotFoundError(SubmissionModelError):
    pass

class SubmissionNotOneError(SubmissionModelError):
    pass

class SubmissionNoContextSelectedError(SubmissionModelError):
    pass

class SubmissionContextNotFoundError(SubmissionModelError):
    pass

class SubmissionContextNotOneError(SubmissionModelError):
    pass

class Submission(TXModel):
    """
    This represents a temporary submission. Submissions should be stored here
    until they are transformed into a Tip.
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class Submission")
    __storm_table__ = 'submission'

    submission_gus = Unicode(primary=True)

    fields = Pickle()

    context_selected = Pickle()

    folder_gus = Unicode()
    folder = Reference(folder_gus, Folder.folder_gus)

    creation_time = Date()

    @transact
    def new(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "new")
        store = self.getStore()

        submission_gus = idops.random_submission_gus(False)
        creation_time = gltime.utcDateNow()

        submission = Submission()
        submission.submission_gus = submission_gus
        submission.creation_time = creation_time

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
        #safeCommit(store, ("(new %s)" % submission_gus) )
        store.close()

        return response

    @transact
    def add_file(self, submission_gus, file_name=None):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "add_file", "submission_gus", submission_gus , "file_name", file_name )
        store = self.getStore()
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

        store.commit()
        #safeCommit(store, ("(store %s)" % file_name) )
        # remind -- rollback operation need to be used when an exception different from
        # lock is raised.
        """
        try:
            store.commit()
        except Exception, e:
            log.exception("[E]: %s %s " % (__file__, __name__), "Submission", "add_file", "submission_gus", submission_gus, "file_name", file_name )
            store.rollback()
            store.close()
            raise SubmissionModelError(e)
        """

        log.debug("Added file %s to %s" % (submission_gus, file_name))
        store.close()
        return new_file_gus

    @transact
    def update_fields(self, submission_gus, fields):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "update_fields", "submission_gus", submission_gus, "fields", fields )

        # XXX: If we re-enable this store = self.getStore we end-up after submission of files in the error
        # "Database is locked". We should identify before that update_fields,  in create_tips why the database is not properly closed

        store = self.getStore()
        #store = safeGetStorage(self, ("(update_fields %s" % submission_gus) )
        try:
            s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError, e:
            # XXX these log lines will be removed in the near future
            log.err("update_fields: Problem looking up %s" % submission_gus)
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

        store.commit()
        #safeCommit(store, ("(update_fields %s)" % submission_gus) )
        # idem as before
        """
        try:
            store.commit()
        except Exception, e:
            log.exception("[E]: %s %s " % (__file__, __name__), "Submission", "update_fields", "submission_gus", submission_gus, "fields", fields )
            store.rollback()
            store.close()
            raise SubmissionModelError(e)
        """
        store.close()


    @transact
    def select_context(self, submission_gus, context):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "select-context", "submission_gus", submission_gus, "context", context )
        store = self.getStore()
        #store = safeGetStorage(self, ("(select_context %s" % submission_gus) )
        try:
            s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError, e:
            # XXX these log lines will be removed in the near future
            log.msg("Problem looking up %s" % submission_gus)
            log.msg(e)
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        s.context_selected = context

        store.commit()
        #safeCommit(store, ("(select_context %s)" % submission_gus) )
        # idem as before
        """
        try:
            store.commit()
        except Exception, e:
            log.debug("[E]: %s %s " % (__file__, __name__), "Submission", "select_context", "submission_gus", submission_gus, "context", context )
            store.rollback()
            store.close()
            raise SubmissionModelError(e)
        """
        store.close()

    # TODO def select_receiver


    @transact
    def status(self, submission_gus):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "status", "submission_gus", submission_gus )

        store = self.getStore()
        #store = safeGetStorage(self, ("(status %s" % submission_gus) )

        try:
            s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError, e:
            store.rollback()
            store.close()
            raise SubmissionNotOneError

        if not s:
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        status = {'context_selected': s.context_selected,
                  'fields': s.fields}
                # TODO 'creation_time' and 'expiration_time'

        store.commit()
        #safeCommit(store, ("(status %s)" % submission_gus) )

        store.close()
        return status

    @transact
    def create_tips(self, submission_gus, receipt):
        """
        this function is became simply unmaintainable
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "create_tips", "submission_gus", submission_gus, "receipt", receipt )
        log.debug("Creating tips for %s" % submission_gus)

        store = self.getStore()
        #store = safeGetStorage(self, ("(create_tips %s" % submission_gus) )

        try:
            submission = store.find(Submission,
                            Submission.submission_gus==submission_gus).one()
        except NotOneError, e:
            log.msg("Problem creating tips for %s" % submission_gus)
            log.msg(e)
            store.rollback()
            store.close()
            # XXX if this happens we probably have to delete one row in the DB
            raise SubmissionModelError("Collision detected! HELP THE WORLD WILL END!")
        except Exception, e:
            log.err("Other random exception")
            log.err(e)
            store.rollback()
            store.close()
            raise SubmissionModelError

        if not submission:
            # XXX investigate
            # this can never happen, would be catch by NotOneError before
            store.rollback()
            store.close()
            log.msg("Did not find the %s submission" % submission_gus)
            raise SubmissionNotFoundError

        if not submission.context_selected:
            store.rollback()
            store.close()
            log.msg("Did not find the context for %s submission" % submission_gus)
            raise SubmissionNoContextSelectedError

        try:
            context = store.find(Context,
                    Context.context_gus == submission.context_selected).one()
        except NotOneError, e:
            # XXX will this actually ever happen?
            # Investigate!
            # CAN) yes, is not checked in update_fields, and here need to be checked, (also the fields,
            #      need to be compared/validated with
            store.rollback()
            store.close()
            raise SubmissionContextNotOneError

        if not context:
            log.msg("Did not find the context for %s submission" % submission_gus)
            # shall be the rollback to create a logest timeout, and then make lock the other operation ?
            store.rollback()
            store.close()
            raise SubmissionContextNotFoundError

        log.debug("Creating internal tip")
        try:
            internal_tip = InternalTip()
            internal_tip.fields = submission.fields
            internal_tip.context_gus = submission.context_selected
            store.add(internal_tip)
        except Exception, e:
            log.err(e)
            store.rollback()
            store.close()
            raise SubmissionModelError

        log.debug("Created internal tip %s" % internal_tip.context_gus)

        if submission.folder:
            log.debug("Creating submission folder table %s" % submission.folder_gus)
            folder = submission.folder
            folder.internaltip = internal_tip

            store.add(folder) # copyed from the commented block before, for put a:
            #safeCommit(store, ("(create_tips / folder %s)" % submission_gus) )
            store.commit()
            """
            try:
                store.add(folder)
                store.commit()
            except Exception, e:
                log.err(e)
                store.rollback()
                store.close()
                raise SubmissionModelError
            """

            log.debug("Submission folder created withour error")
        else:
            print "I don't believe this is possible, actually, submission.folder is created on new()"
            # XXX, and I don't get why folder_gus is returned by new():
            # because file uploader # use submission_gus as reference, do not need folder_gus too.
            # because if someone want restore an upload, use the file_gus instead of folder_gus

        log.debug("Creating tip for whistleblower")
        whistleblower_tip = Tip()
        whistleblower_tip.internaltip = internal_tip
        whistleblower_tip.address = receipt
                # holy shit XXX here
        store.add(whistleblower_tip)
        log.debug("Created tip with address %s" % whistleblower_tip.address)

        #receiver_tips = context.create_receiver_tips(internal_tip)
        log.debug("Looking up receivers")
        for receiver in context.receivers:
            log.debug("[D] %s %s " % (__file__, __name__), "Submission", "create_tips", "Creating tip for %s" % receiver.receiver_gus)
            receiver_tip = ReceiverTip()
            receiver_tip.internaltip = internal_tip
            receiver_tip.new(receiver.receiver_gus)
            store.add(receiver_tip)
            log.debug("Tip created")

            """

            At the moment the scheduler queue is bugged,


            log.debug("Creating delivery jobs")
            delivery_job = Delivery()
            delivery_job.submission_gus = submission_gus
            delivery_job.receipt_id = receiver_tip.address
            work_manager.add(delivery_job)

            log.debug("Added delivery to %s to the work manager" % receiver.receiver_gus)

            notification_job = Notification()
            notification_job.address = receiver.name
            notification_job.receipt_gus = receiver_tip.address
            work_manager.add(notification_job)
            """

        log.debug("Deleting the temporary submission %s" % submission.submission_gus)

        store.remove(submission)
        # maybe also this operation can give the lock problem

        store.commit()
        #safeCommit(store, ("(create_tips / all the stuff %s)" % submission_gus) )

        """
        try:
            store.commit()
        except Exception, e:
            log.exception("[E]: %s %s " % (__file__, __name__), "Submission", "add_file", "submission_gus", type(submission_gus), "file_name", type(file_name), "Could not create submission" )
            log.err(e)
            store.rollback()
            store.close()
        """

        log.debug("create_tips complete, commit done, closing storage")
        store.close()

