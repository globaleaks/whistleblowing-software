# -*- coding: UTF-8
#   submission
#   **********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Implements a GlobaLeaks submission.

from twisted.internet.defer import returnValue, inlineCallbacks

from globaleaks import db
from globaleaks.db import models, transactor
from globaleaks.utils import idops
from globaleaks import Processor

from globaleaks.rest import answers
from globaleaks.rest.errors import GLErrorCode

import pickle

def mydirtydebug(whoami, safereq, uriargs, args, kw):
    print "[:>]", whoami, safereq, type(uriargs), uriargs, args, kw


class Submission(Processor):
    handler = None
    model = models.Submission() # idem, non viene mai usata
    transactor = transactor # TO be removed  ?

    @inlineCallbacks
    def new_GET(self, safereq, *uriargs):
        """
        U2, Creates an empty submission and returns the ID to the WB.
        """
        self.handler.status_code = 201

        new_submission = models.Submission()
        new_submission.submission_id = unicode(idops.random_submission_id(False))
        new_submission.folder_id = 0

        # --------------------------------------
        # In a stable implementation, .fields would be set with the
        # default taken by context
        # In this case, are used the dummy values
        # 'fields' and 'receivers' both
        from globaleaks.messages.dummy import shared, answers, requests

        fake_submission = requests.submissionStatusPost
        new_submission.fields = fake_submission['fields']

        fake_receivers = [idops.random_receiver_id(),
                          idops.random_receiver_id(),
                          idops.random_receiver_id(),
                          idops.random_receiver_id()]
        new_submission.receivers = fake_receivers

        output = {"submission_id": new_submission.submission_id}

        yield new_submission.save()

        # dummy.SUBMISSION_NEW_GET(output)
        returnValue(output)

    @inlineCallbacks
    def status_GET(self, safe_req, submission_id):
        """
        U3, refresh whistleblower client with the previously uploaded data
        """

        submission = yield db.find_one(models.Submission,
                models.Submission.submission_id==submission_id)

        print "Found submission!"
        print submission
        # XXX remove this in future
        from globaleaks.messages.dummy import shared, answers, requests

        self.handler.status_code = 200
        status = {'receivers_selected': submission.receivers,
                  'fields': submission.fields}
        print status
        returnValue(status)

    """
    status handle the group receiver selection
        (if enabled in the context settings)
    handle the fields submission
        (import the fields in the temporary submission_id entry)
    """
    @inlineCallbacks
    def status_POST(self, safe_req, submission_id, *uriargs):
        """
        U3, update the whistleblower stored data, expect in safereq
        fields: an array of formFieldsDict
        receivers: an array of receiverID
        verify in the local settings if the receivers shall be choosen by WB
        if some fields are required, is not check here.
        """

        # safereq.fields.convertToPickle() -- TODO

        # print "pickle: ", pickle.dumps(safereq.fields)

        # return self.status_GET(uriargs, safereq, arg, kw)
        res = yield self.status_GET(safe_req, submission_id, *uriargs)
        returnValue(res)


    # def finalize_POST(self, submission_id, **form_fields):
    # U4
    @inlineCallbacks
    def finalize_POST(self, safereq, submission_id, *uriargs):
        """
        Finalize the submission and create data inside of the database,
        perform checks if the required fiels has been set
        """
        submission = yield db.find_one(models.Submission,
                models.Submission.submission_id==submission_id)

        receipt_id = unicode(idops.random_receipt_id())
        internal_tip = models.InternalTip()
        internal_tip.fields = submission.fields

        self.handler.status_code = 201
        yield internal_tip.save()

        whistleblower_tip = models.Tip()
        whistleblower_tip.internaltip_id = internal_tip.id
        whistleblower_tip.address = receipt_id

        yield whistleblower_tip.save()

        tip = yield db.find_one(models.Tip, models.Tip.address==receipt_id)

        inttip = yield tip.internaltip()
        receipt = {"receipt": receipt_id}
        returnValue(receipt)

    # U5
    def files_GET(self, submission_id, *uriarg):
        """
        retrive the status of the file uploaded, the
        submission_id has only one folder during the first
        submission

        XXX remind: in the API-interface is not yet defined
        """
        from globaleaks.messages.dummy import shared, answers, requests

        return shared.fileDicts[0]

    def files_PUT(self, submission_id, *uriarg):
        """
        Take the new data and append to the file, contain sync,
        need to be checked prorperly
        """
        return self.files_GET(submission_id, *uriarg)

    def files_POST(self, submission_id, *uriarg):
        """
        :description, dict of text describig the file uploaded
         (or not yet complete) by PUT, every time a new
         files_POST is reached, all the files description is
         updated
        """
        return self.files_GET(submission_id, *uriarg)

    def files_DELETE(self, submission_id, *arg, **kw):
        """
        :filename, remove a complete or a partial uploaded
         file
        """
        return self.files_GET(submission_id, *uriarg)
