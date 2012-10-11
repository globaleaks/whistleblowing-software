# -*- coding: UTF-8
#   submission
#   **********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Implements a GlobaLeaks submission.

from twisted.internet.defer import returnValue, inlineCallbacks

from globaleaks.db import models, transactor
from globaleaks.utils import idops
from globaleaks import Processor

from globaleaks.utils.dummy import dummy_answers as dummy
from globaleaks.utils import recurringtypes as GLT
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
    def new_GET(self, uriargs, safereq, *arg, **kw):
        """
        U2, Creates an empty submission and returns the ID to the WB.
        """
        self.handler.status_code = 201

        newSubmsn = models.Submission()
        newSubmsn.submission_id =  idops.random_submission_id(False)
            # need to be unicode ?
        newSubmsn.folder_id = 0

        # --------------------------------------
        # In a stable implementation, .fields would be set with the
        # default taken by context
        # In this case, are used the dummy values
        # 'fields' and 'receivers' both
        from globaleaks.utils.dummy import dummy_shared

        testField1 = GLT.formFieldsDict()
        dummy_shared._formFieldsDict0(testField1)
        testField2 = GLT.formFieldsDict()
        dummy_shared._formFieldsDict1(testField1)

        fakeFieldDict = {}
        fakeFieldDict.update({'fields' : [ testField1.unroll(),  testField2.unroll() ]})
        newSubmsn.fields = pickle.dumps(fakeFieldDict)

        fakeReceiversDict = {}
        fakeReceiversDict.update({'receivers' : [ idops.random_receiver_id(),
                                                 idops.random_receiver_id(),
                                                 idops.random_receiver_id(),
                                                 idops.random_receiver_id() ] })
        newSubmsn.receivers = pickle.dumps(fakeReceiversDict)
        # --------------------------------------

        output = answers.newSubmission()
        output.submission_id = newSubmsn.submission_id

        yield newSubmsn.save()

        # dummy.SUBMISSION_NEW_GET(output)
        returnValue(output.unroll())

    def status_GET(self, uriargs, safereq, *arg, **kw):
        """
        U3, refresh whistleblower client with the previously uploaded data
        """
        mydirtydebug(__name__, safereq, uriargs, arg, kw )

        resumed = models.Submission()
        try:
            resumed.resume(uriargs)
        except AttributeError:
            self.handler.status_code = 404 # (Not Found)
            returnValue(answers.errorMessage(404, GLErrorCode.invalid_sID).unroll())

        # XXX remove this in future
        print resumed

        self.handler.status_code = 200
        output = answers.submissionStatus()
        # dummy.SUBMISSION_STATUS_GET(output)
        returnValue(output.unroll())

    """
    status handle the group receiver selection
        (if enabled in the context settings)
    handle the fields submission
        (import the fields in the temporary submission_id entry)
    """
    def status_POST(self, uriargs, safereq, *arg, **kw):
        """
        U3, update the whistleblower stored data, expect in safereq
        fields: an array of formFieldsDict
        receivers: an array of receiverID
        verify in the local settings if the receivers shall be choosen by WB
        if some fields are required, is not check here.
        """
        mydirtydebug(__name__, uriargs, safereq, arg, kw)

        # safereq.fields.convertToPickle() -- TODO

        # print "pickle: ", pickle.dumps(safereq.fields)

        # return self.status_GET(uriargs, safereq, arg, kw)
        returnValue(self.status_GET(uriargs, safereq, arg, kw))


#    def finalize_POST(self, submission_id, **form_fields):
    # U4
    @inlineCallbacks
    def finalize_POST(self, uriargs, safereq, *arg, **kw):
        """
        Finalize the submission and create data inside of the database,
        perform checks if the required fiels has been set
        """
        mydirtydebug(__name__, uriargs, safereq, arg, kw)

        resumed = models.Submission()
        resumed.resume(uriargs)

        # XXX remove this in future
        print resumed

        self.handler.status_code = 406 # (Not Acceptable)
        returnValue(answers.errorMessage(406, GLErrorCode.incomplete_fields).unroll())

        receipt_id = unicode(idops.random_receipt_id())
        internal_tip = models.InternalTip()
        internal_tip.fields = pickle.dumps( {'shittest': 'isatest'} )

        self.handler.status_code = 201
        yield internal_tip.save()

        whistleblower_tip = models.Tip()
        whistleblower_tip.internaltip_id = internal_tip.id
        whistleblower_tip.address = receipt_id

        yield whistleblower_tip.save()

        ret = answers.finalizeSubmission()
        returnValue(ret.unroll())

    # U5
    def files_GET(self, submission_id, *arg, **kw):
        """
        retrive the status of the file uploaded, the
        submission_id has only one folder during the first
        submission

        XXX remind: in the API-interface is not yet defined
        """
        ret = GLT.fileDict()
        dummy.SUBMISSION_FILES_GET(ret)
        return ret.unroll()

    def files_PUT(self, submission_id, *arg, **kw):
        """
        Take the new data and append to the file, contain sync,
        need to be checked prorperly
        """
        return files_GET(arg, kw)

    def files_POST(self, submission_id, *arg, **kw):
        """
        :description, dict of text describig the file uploaded
         (or not yet complete) by PUT, every time a new
         files_POST is reached, all the files description is
         updated
        """
        return files_GET(submission_id, *arg, **kw)

    def files_DELETE(self, submission_id, *arg, **kw):
        """
        :filename, remove a complete or a partial uploaded
         file
        """
        return files_GET(submission_id, *arg, **kw)
