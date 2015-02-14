# -*- coding: UTF-8
#
#   submission
#   **********
#
#   Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission URI

import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.models import Context, InternalTip, Receiver, WhistleblowerTip, \
    Node, InternalFile
from globaleaks import security
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin import db_get_context_steps
from globaleaks.handlers.authentication import transport_security_check, unauthenticated
from globaleaks.utils.token import Token, TokenList
from globaleaks.rest import requests
from globaleaks.utils.utility import log, utc_future_date, datetime_now, datetime_to_ISO8601
from globaleaks.third_party import rstr
from globaleaks.rest import errors
from globaleaks.anomaly import Alarm

def wb_serialize_internaltip(internaltip):

    response = {
        'id' : internaltip.id,
        'context_id': internaltip.context_id,
        'creation_date' : datetime_to_ISO8601(internaltip.creation_date),
        'expiration_date' : datetime_to_ISO8601(internaltip.expiration_date),
        'wb_steps' : internaltip.wb_steps,
        'download_limit' : internaltip.download_limit,
        'access_limit' : internaltip.access_limit,
        'mark' : internaltip.mark,
        'files' : [f.id for f in internaltip.internalfiles],
        'receivers' : [r.id for r in internaltip.receivers]
    }

    return response

def db_create_whistleblower_tip(store, submission_desc):
    """
    The plaintext receipt is returned only now, and then is
    stored hashed in the WBtip table
    """
    wbtip = WhistleblowerTip()

    node = store.find(Node).one()

    return_value_receipt = unicode( rstr.xeger(node.receipt_regexp) )
    wbtip.receipt_hash = security.hash_password(return_value_receipt, node.receipt_salt)

    wbtip.access_counter = 0
    wbtip.internaltip_id = submission_desc['id']
    store.add(wbtip)

    return return_value_receipt

@transact
def create_whistleblower_tip(*args):
    return db_create_whistleblower_tip(*args)

def import_receivers(store, submission, receiver_id_list):
    context = submission.context

    # Clean the previous list of selected Receiver
    for prevrec in submission.receivers:
        try:
            submission.receivers.remove(prevrec)
        except Exception as excep:
            log.err("Unable to remove receiver from Tip, before new reassignment")
            raise excep

    # and now clean the received list and import the new Receiver set.
    receiver_id_list = set(receiver_id_list)

    if not len(receiver_id_list):
        log.err("Receivers required to be selected, not empty")
        raise errors.SubmissionFailFields("Needed almost one Receiver selected")

    if context.maximum_selectable_receivers and \
                    len(receiver_id_list) > context.maximum_selectable_receivers:
        raise errors.InvalidInputFormat("Provided an invalid number of Receivers")

    for receiver_id in receiver_id_list:
        try:
            receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        except Exception as excep:
            log.err("Receiver requested (%s) can't be found: %s" %
                    (receiver_id, excep))
            raise errors.ReceiverIdNotFound

        if context not in receiver.contexts:
            raise errors.InvalidInputFormat("Forged receiver selection, you fuzzer! <:")

        try:
            if not GLSetting.memory_copy.allow_unencrypted and \
                    receiver.gpg_key_status != u'enabled':
                log.err("Encrypted only submissions are supported. Cannot select [%s]" % receiver_id)
                continue
            submission.receivers.add(receiver)
        except Exception as excep:
            log.err("Receiver %s can't be assigned to the tip [%s]" % (receiver_id, excep) )
            continue

        log.debug("+receiver [%s] In tip (%s) #%d" %\
                (receiver.name, submission.id, submission.receivers.count() ) )
   
    if submission.receivers.count() == 0:
        log.err("Receivers required to be selected, not empty")
        raise errors.SubmissionFailFields("Needed at least one Receiver selected [2]")

# Remind: it's a store without @transaction because called by a @ŧransact
def import_files(store, submission, files):
    """
    @param submission: the Storm obj
    @param files: the list of InternalFiles UUIDs
    @return:
        Look if all the files specified in the list exist,
        Look if the context *require* almost a file, raise
            an error if missed
    """
    for file_id in files:
        try:
            ifile = store.find(InternalFile, InternalFile.id == unicode(file_id)).one()
        except Exception as excep:
            log.err("Storm error, not found %s file in import_files (%s)" %
                    (file_id, excep))
            raise errors.FileIdNotFound

        ifile.internaltip_id = submission.id

def verify_fields_recursively(fields, wb_fields):
    for f in fields:
        if f not in wb_fields:
            raise errors.SubmissionFailFields("missing field (no structure present): %s" % f)

        if fields[f]['required'] and ('value' not in wb_fields[f] or
                                      wb_fields[f]['value'] == ''):
            raise errors.SubmissionFailFields("missing required field (no value provided): %s" % f)

        if isinstance(wb_fields[f]['value'], unicode):
            if len(wb_fields[f]['value']) > GLSetting.memory_copy.maximum_textsize:
                raise errors.InvalidInputFormat("field value overcomes size limitation")

        indexed_fields  = {}
        for f_c in fields[f]['children']:
            indexed_fields[f_c['id']] = copy.deepcopy(f_c)

        indexed_wb_fields = {}
        for f_c in wb_fields[f]['children']:
            indexed_wb_fields[f_c['id']] = copy.deepcopy(f_c)

        verify_fields_recursively(indexed_fields, indexed_wb_fields)

    for wbf in wb_fields:
        if wbf not in fields:
            raise errors.SubmissionFailFields("provided unexpected field %s" % wbf)

def verify_steps(steps, wb_steps):
    indexed_fields  = {}
    for step in steps:
        for f in step['children']:
            indexed_fields[f['id']] = copy.deepcopy(f)

    indexed_wb_fields = {}
    for step in wb_steps:
        for f in step['children']:
            indexed_wb_fields[f['id']] = copy.deepcopy(f)

    return verify_fields_recursively(indexed_fields, indexed_wb_fields)


def db_finalize_submission(store, context_id, request, language):

    print "XXX", context_id

    context = store.find(Context, Context.id == unicode(request['context_id'])).one()
    if not context:
        log.err("Context requested: [%s] not found!" % request['context_id'])
        raise errors.ContextIdNotFound

    submission = InternalTip()

    submission.access_limit = context.tip_max_access
    submission.download_limit = context.file_max_download
    submission.expiration_date = utc_future_date(seconds=context.tip_timetolive)
    submission.context_id = context.id
    submission.creation_date = datetime_now()
    submission.mark = u'finalize'  # Finalized

    try:
        store.add(submission)
    except Exception as excep:
        log.err("Storm/SQL Error: %s (create_submission)" % excep)
        raise errors.InternalServerError("Unable to commit on DB")

    try:
        import_files(store, submission, request['files'])
    except Exception as excep:
        log.err("Submission create: files import fail: %s" % excep)
        raise excep

    try:
        wb_steps = request['wb_steps']

        steps = db_get_context_steps(store, context.id, language)
        verify_steps(steps, wb_steps)

        submission.wb_steps = wb_steps
    except Exception as excep:
        log.err("Submission create: fields validation fail: %s" % excep)
        raise excep

    try:
        import_receivers(store, submission, request['receivers'])
    except Exception as excep:
        log.err("Submission create: receivers import fail: %s" % excep)
        raise excep

    submission_dict = wb_serialize_internaltip(submission)
    return submission_dict


@transact_ro
def get_submission(store, submission_id):
    submission = store.find(InternalTip, InternalTip.id == unicode(submission_id)).one()

    if not submission:
        log.err("Invalid Submission requested %s in GET" % submission_id)
        raise errors.SubmissionIdNotFound

    return wb_serialize_internaltip(submission)


class SubmissionCreate(BaseHandler):
    """
    This class Request a token to create a submission. is kept the naming with "Create"
    suffix for internal globaleaks convention, but this handler do not interact with
    Database, InternalTip, submissions.
    return a submission_id, keep track of the request time, in order to , usable in update operation
    """

    @transport_security_check('wb')
    @unauthenticated
    def post(self, context_id):
        """
        Request: wbSubmissionDesc
        Response: wbSubmissionDesc
        Errors: ContextIdNotFound, InvalidInputFormat, SubmissionFailFields

        This creates an empty submission for the requested context,
        and returns submissionStatus with empty fields and a Submission Unique String,
        This is the unique token used during the submission procedure.
        header session_id is used as authentication secret for the next interaction.
        expire after the time set by Admin (Context dependent setting)

        --- has to became:
        Request: empty
        Response: wbSubmissionDesc + Token
        Errors: None

        This create a Token, require to complete the submission later
        """

        token = Token('submission', context_id, debug=True)
        token.set_difficulty(Alarm().get_token_difficulty())
        token_answer = token.serialize_token()


        # {'hashcash': False,
        #  'usages': 1,
        #  'start_validity': '2015-02-09T13:23:44.325796Z',
        #  'end_validity': '2015-02-09T13:26:44.325796Z',
        #  'token_id': u'sl0nEmLtxaogJ1er4B2TWHUdv9RAmD6TusKgL8d97u',
        #  'type': 'submission', 'g_captcha': False,
        #  'h_captcha': False,
        #  'creation_date': '2015-02-09T13:22:44.325796Z'}

        # change, put the post_transact + finalize in PUT and removed from here
        # request = self.validate_message(self.request.body, requests.wbSubmissionDesc)

        token_answer.update({'submission_id': token_answer['token_id'] })
        token_answer.update({'id': token_answer['token_id'] })
        token_answer.update({'files': [] })
        token_answer.update({'context_id': context_id})

        # preset the answers from the captcha stuff, to success input validation
        token_answer.update({'human_solution': 0})

        import pprint

        # {'hashcash': False,
        #  'usages': 1,
        #  'start_validity': '2015-02-09T13:23:44.325796Z',
        #  'end_validity': '2015-02-09T13:26:44.325796Z',
        #  'token_id': u'sl0nEmLtxaogJ1er4B2TWHUdv9RAmD6TusKgL8d97u',
        #  'type': 'submission', 'g_captcha': False,
        #  'h_captcha': False,
        #  'creation_date': '2015-02-09T13:22:44.325796Z'}

        # change, put the post_transact + finalize in PUT and removed from here
        # request = self.validate_message(self.request.body, requests.wbSubmissionDesc)
        print token_answer['token_id']

        token_answer.update({'submission_id': token_answer['token_id'] })
        token_answer.update({'id': token_answer['token_id'] })
        token_answer.update({'files': [] })
        # tmp hackish, I can copy the context receive via get, in order to make
        # SubmissionRequest context dependent in the URL (finally, holy fuck)
        token_answer.update({'context_id': context_id})

        self.set_status(201) # Created
        self.finish(token_answer)


class SubmissionInstance(BaseHandler):
    """
    This is the interface for create, populate and complete a submission.
    Relay in the client-server update and exchange of the submissionStatus message.
    """

    @transport_security_check('wb')
    @unauthenticated
    @inlineCallbacks
    def put(self, context_id, token_id):
        """
        Parameter: token_id
        Request: wbSubmissionDesc
        Response: wbSubmissionDesc
        Errors: ContextIdNotFound, InvalidInputFormat, SubmissionFailFields, SubmissionIdNotFound, SubmissionConcluded

        PUT update the submission and finalize if requested.
        """
        @transact
        def put_transact(store, token_id, request, language):

            status = db_finalize_submission(store, token_id, request, self.request.language)

            receipt = db_create_whistleblower_tip(store, status)
            status.update({'receipt': receipt})

            return status

        request = self.validate_message(self.request.body, requests.wbSubmissionDesc)
        import pprint
        pprint.pprint(request.keys())

        # the .get method raise an exception if the token is invalid
        TokenList.get(token_id)
        token = TokenList.token_dict[token_id]

        log.debug("Token received: %s" % token)
        # raise an error if the usage is too early for the token
        token.timedelta_check()

        if not token.context_associated == context_id:
            raise errors.InvalidInputFormat("Token context unaligned with REST url")

        assert request['finalize'], "Wrong GLClient logic"

        # check if token has been properly solved
        if token.graph_captcha is not False:
            print "GC!, NYI", token.graph_captcha
        if token.proof_of_work is not False:
            print "PoW!, NYI", token.proof_of_work
        if token.human_captcha is not False:
            print "checking HC:", token.human_captcha
            token.human_captcha_check(request['human_solution'])

        status = yield put_transact(token_id, request, self.request.language)

        self.set_status(202) # Updated --> created
        self.finish(status)


