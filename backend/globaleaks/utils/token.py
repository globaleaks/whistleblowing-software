# -*- coding: UTF-8
#
#   token
#   *****
#
#   Implements a GlobaLeaks security token, to prevent resources exhaustion
#   operation by anonymous user.

import base64
from StringIO import StringIO
from random import randint
from datetime import datetime, timedelta

from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601
from globaleaks.third_party import rstr
from globaleaks.rest import errors
from globaleaks.utils.tempobj import TempObj
from globaleaks.settings import GLSetting

class TokenList:

    token_dict = dict()

    @staticmethod
    def delete(t_id):
        """
        Token can be used only once, so need to be remove after the first usage.
        :param t_id:
        :return:
        """
        if t_id not in TokenList.token_dict:
            raise errors.TokenRequestError("Not found")

        del TokenList.token_dict[t_id]

    @staticmethod
    def get(t_id):
        if t_id not in TokenList.token_dict:
            raise errors.TokenRequestError("Not found")

        return TokenList.token_dict[t_id]


# needed in order to allow UT override
reactor = None

class Token(TempObj):

    SUBMISSION_MINIMUM_DURATION = 0
    SUBMISSION_MAXIMUM_DURATION = 3600 * 4
    MAXIMUM_ATTEMPTS_PER_TOKEN = 3
    MAXIMUM_UPLOADS_PER_TOKEN = 20

    def __init__(self, token_kind, context_id):
        """
        token_kind assumes currently only value 'submission.

        we plan to add other kinds like 'file'.

        """
        # Remind: this is just for developers, because if a clean house
        # is a sign of a waste life, a Token object without shortcut
        # is a sign of a psyco life. (vecnish!)
        if GLSetting.devel_mode:
            self.start_validity_secs = 0

        self.kind = token_kind

        # both 'validity' variables need to be expressed in seconds
        self.start_validity_secs = Token.SUBMISSION_MINIMUM_DURATION
        self.end_validity_secs = Token.SUBMISSION_MAXIMUM_DURATION

        self.remaining_allowed_attempts = Token.MAXIMUM_ATTEMPTS_PER_TOKEN
        self.remaining_allowed_uploads = Token.MAXIMUM_UPLOADS_PER_TOKEN

        # creation_date of token assignment
        self.creation_date = datetime.utcnow()

        # in the future, difficulty can be trimmed on context basis too
        self.context_associated = context_id

        # to keep track of the file uploaded associated
        self.files_uploaded = []

        self.token_id = rstr.xeger(r'[A-Za-z0-9]{42}')

        # initialization
        self.human_captcha = False
        self.proof_of_work = False
        self.graph_captcha = False

        TempObj.__init__(self,
                         TokenList.token_dict,
                         # token ID:
                         self.token_id,
                         # seconds of validity:
                         self.start_validity_secs + self.end_validity_secs,
                         reactor)

    def file_upload_usage(self):
        """
        This function is called every time a file is uploaded and causes
        a decrement on a counter.
        When the counter reaches 0, no further uploads are allowed.

        :return: None or raise an error
        """
        if not self.remaining_allowed_uploads:
            raise errors.TokenRequestError("Too much files uploaded")

        self.remaining_allowed_uploads -= 1

        log.debug("From a maximum of %d files, this token has %d slots" % (
            Token.MAXIMUM_UPLOADS_PER_TOKEN, self.remaining_allowed_uploads))

    def associate_file(self, fileinfo):
        self.files_uploaded.append(fileinfo)

    def touch(self):
        # On token objects validity postponing is denied
        return

    def __repr__(self):
        test_desc = ""
        dump_attr = ['graph_captcha', 'human_captcha', 'proof_of_work']

        for a in dump_attr:
            if getattr(self, a):
                test_desc = "%s[H:%s]" % (test_desc,  getattr(self, a)['question'])

        token_string = "Token %s with %s" % (self.kind,
                                             test_desc if len(test_desc) else "No test")

        return token_string

    def serialize_token(self):

        return {
            'token_id': self.token_id,
            'creation_date': datetime_to_ISO8601(self.creation_date),
            'start_validity_secs': datetime_to_ISO8601(self.creation_date +
                                                  timedelta(seconds=self.start_validity_secs) ),
            'end_validity_secs': datetime_to_ISO8601(self.creation_date +
                                                timedelta(seconds=self.end_validity_secs) ),
            'remaining_allowed_attempts': self.remaining_allowed_attempts,
            'remaining_allowed_uploades': self.remaining_allowed_uploads,
            'type': self.kind,
            'g_captcha': self.graph_captcha['question'] if self.graph_captcha else False,
            'h_captcha': self.human_captcha['question'] if self.human_captcha else False,
            'proof_of_work': self.proof_of_work['question'] if self.proof_of_work else False,
        }

    def set_difficulty(self, problems_dict):
        """
        @problems_dict: arrive directly from anomaly.Alarm.get_token_difficulty
            and in a future enhancement we can implement set_difficult in
            FileToken or SubmissionToken and here the shared element.
        """

        if problems_dict['human_captcha']:
            random_a = randint(1, 10)
            random_b = randint(1, 10)

            self.human_captcha = {
                'question': u"%d + %d" % (random_a, random_b),
                'answer': u"%d" % (random_a + random_b)
            }

        if problems_dict['proof_of_work']:
            # still not implemented
            pass

        if problems_dict['graph_captcha']:
            # still not implemented
            pass

    def timedelta_check(self):
        """
        This timedelta check verify that the current time fit between
        the starting_

        """
        now = datetime_now()
        start = (self.creation_date + timedelta(seconds=self.start_validity_secs))
        if not start < now:
            log.debug("creation + validity (%d) = %s < now %s, still to early" %
                      (self.start_validity_secs, start, now))
            raise errors.TokenRequestError("Too early to use this token")


        # This will never happen after integration of self expiring objects.
        end = (self.creation_date + timedelta(self.end_validity_secs) )
        if now > end:
            log.debug("creation + end_validity (%d) = %s > now %s, too late" %
                      (self.end_validity_secs, start, now))
            raise errors.TokenRequestError("Too late to use this token")

        # If the code reach here, the time delta is good.

    def human_captcha_check(self, resolved_human_captcha):
        if not self.human_captcha:
            return

        if int(self.human_captcha['answer']) != int(resolved_human_captcha):
            log.debug("Failed human captcha: expected %s got %s" % (
                (self.human_captcha['answer'], resolved_human_captcha)
            ))
            raise errors.TokenRequestError("Failed Human captcha")
        else:
            log.debug("Successful Human captcha resolution: %s" %
                      resolved_human_captcha)

    def graph_captcha_check(self, resolved_graph_captcha):

        if not self.graph_captcha:
            return

        if self.graph_captcha['answer'] != resolved_graph_captcha:
            log.debug("Failed graph captcha: expected %s got %s" % (
                (self.graph_captcha['answer'], resolved_graph_captcha)
            ))
            raise errors.TokenRequestError("Failed Graphical captcha")
        else:
            log.debug("Successful Graphical captcha resolution: %s" %
                      resolved_graph_captcha)

    def proof_of_work_check(self, resolved_proof_of_work):
        pass


    def validate(self, request):
        """
        @request is the submission;
          it contains the *_solution fields.
          if some fields are currently missing, it's because they are
          not yet implemented.
        """

        if not self.remaining_allowed_attempts:
            TokenList.delete(self.id)
            raise errors.TokenRequestError("Too many attepts")
        else:
            log.debug("Token has %d available tries" % self.remaining_allowed_attempts)

        # any of these can raise an exception if check fail
        try:
            self.timedelta_check()

            if self.human_captcha is not False:
                self.human_captcha_check(request['human_solution'])

            if self.graph_captcha is not False:
                assert False, "Graphical Captcha! NotYetImplemented"

            # Raise an exception if, by mistake, we ask for something not yet supported
            if self.proof_of_work is not False:
                assert False, "Proof of Wor<M-F12>k! NotYetImplemented"

        except errors.GLException as gle:
            log.debug("Error triggered in Token validation, remaining attempts %d => %d" % (
                self.remaining_allowed_attempts, self.remaining_allowed_attempts - 1))
            self.remaining_allowed_attempts -= 1
            raise

        # if the code flow reach here, the token is validated
        log.debug("Token validated properly")
