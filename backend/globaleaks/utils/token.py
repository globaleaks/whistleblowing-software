# -*- coding: UTF-8
#
# token
#   *****
#
#   Implements a GlobaLeaks security token, to prevent resources exhaustion
#   operation by anonymous user.

from random import randint
from datetime import datetime, timedelta

import os
from globaleaks.anomaly import Alarm

from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601
from globaleaks.rest import errors
from globaleaks.utils.tempdict import TempDict
from globaleaks.settings import GLSettings
from globaleaks.security import sha256, generateRandomKey


class TokenListClass(TempDict):
    def __init__(self, *args, **kwds):
        TempDict.__init__(self, *args, **kwds)

    def get_timeout(self):
        return GLSettings.memory_copy.submission_minimum_delay + \
               GLSettings.memory_copy.submission_maximum_ttl

    def expireCallback(self, item):
        for f in item.uploaded_files:
            try:
                os.remove(f['encrypted_path'])
            except Exception:
                pass

    def get(self, key):
        ret = TempDict.get(self, key)
        if ret == None:
            raise errors.TokenFailure("Not found")

        return ret


TokenList = TokenListClass()


class Token(object):
    MAX_USES = 30

    def __init__(self, token_kind, uses = MAX_USES):
        """
        token_kind assumes currently only value 'submission.

        we plan to add other kinds like 'file'.

        """
        self.id = generateRandomKey(42)

        self.kind = token_kind

        # both 'validity' variables need to be expressed in seconds
        self.start_validity_secs = GLSettings.memory_copy.submission_minimum_delay
        self.end_validity_secs = GLSettings.memory_copy.submission_maximum_ttl

        # Remind: this is just for developers, because if a clean house
        # is a sign of a waste life, a Token object without shortcut
        # is a sign of a psycho life. (vecnish!)
        if GLSettings.devel_mode:
            self.start_validity_secs = 0

        self.remaining_uses = uses

        # creation_date of token assignment
        self.creation_date = datetime.utcnow()

        # to keep track of the file uploaded associated
        self.uploaded_files = []

        # initialization of token configuration
        self.human_captcha = False
        self.graph_captcha = False
        self.proof_of_work = False

        self.generate_token_challenge()

        TokenList.set(self.id, self)

    def expire(self):
        for f in self.uploaded_files:
            try:
                os.remove(f['encrypted_path'])
            except Exception:
                pass

    def associate_file(self, fileinfo):
        self.uploaded_files.append(fileinfo)

    def touch(self):
        # On token objects validity postponing is denied
        return

    def __repr__(self):
        test_desc = ""
        dump_attr = ['graph_captcha', 'human_captcha', 'proof_of_work']

        for a in dump_attr:
            if getattr(self, a):
                test_desc = "%s[H:%s]" % (test_desc, getattr(self, a)['question'])

        token_string = "Token %s for %s [%s]" % (self.id, self.kind, test_desc)

        return token_string

    def serialize(self):
        return {
            'id': self.id,
            'creation_date': datetime_to_ISO8601(self.creation_date),
            'start_validity_secs': self.start_validity_secs,
            'end_validity_secs': self.end_validity_secs,
            'remaining_uses': self.remaining_uses,
            'type': self.kind,
            'graph_captcha': self.graph_captcha['question'] if self.graph_captcha else False,
            'human_captcha': self.human_captcha['question'] if self.human_captcha else False,
            'proof_of_work': self.proof_of_work['question'] if self.proof_of_work else False,
            'human_captcha_answer': 0,
            'graph_captcha_answer': '',
            'proof_of_work_answer': 0
        }

    def generate_token_challenge(self, challenges_dict = None):
        # initialization
        self.human_captcha = False
        self.graph_captcha = False
        self.proof_of_work = False

        if challenges_dict is None:
            challenges_dict = {
                'human_captcha': False,
                'graph_captcha': False,
                'proof_of_work': False
            }

            if Alarm.stress_levels['activity'] >= 1:
                challenges_dict['human_captcha'] = True and GLSettings.memory_copy.enable_captcha

            # a proof of work is always required (if enabled at node level)
            challenges_dict['proof_of_work'] = GLSettings.memory_copy.enable_proof_of_work

        if challenges_dict['human_captcha']:
            random_a = randint(0, 99)
            random_b = randint(0, 99)

            self.human_captcha = {
                'question': u"%d + %d" % (random_a, random_b),
                'answer': u"%d" % (random_a + random_b)
            }

        if challenges_dict['graph_captcha']:
            # still not implemented
            pass

        if challenges_dict['proof_of_work']:
            self.proof_of_work = {
                'question': generateRandomKey(20)
            }

    def timedelta_check(self):
        """
        This timedelta check verify that the current time fits between
        the start validity time and the end validity time.
        """
        now = datetime_now()
        start = (self.creation_date + timedelta(seconds=self.start_validity_secs))
        if not start < now:
            log.debug("creation + validity (%d) = %s < now %s, still to early" %
                      (self.start_validity_secs, start, now))
            raise errors.TokenFailure("Too early to use this token")

        # This will never happen after integration of self expiring objects.
        end = (self.creation_date + timedelta(self.end_validity_secs) )
        if now > end:
            log.debug("creation + end_validity (%d) = %s > now %s, too late" %
                      (self.end_validity_secs, start, now))
            raise errors.TokenFailure("Too late to use this token")

        # If the code reach here, the time delta is good.

    def human_captcha_check(self, resolved_human_captcha):
        try:
            if int(self.human_captcha['answer']) != int(resolved_human_captcha):
                log.debug("Failed human captcha resolution: expected '%s', got '%s'" % (
                    (self.human_captcha['answer'], resolved_human_captcha)
                ))
                return True

            log.debug("Successful human captcha validation: got answer '%s'" % resolved_human_captcha)

            # mark the captcha as solved
            self.human_captcha = False

            return False
        except Exception as e:
            log.debug("Exception while validating the human captcha: %s" % e)
            return True

    def graph_captcha_check(self, resolved_graph_captcha):
        return False

    def proof_of_work_check(self, resolved_proof_of_work):
        """
        :param resolved_proof_of_work: a string, that has to be an integer
        :return:
        """
        HASH_ENDS_WITH = '00'

        try:
            int_pow = int(resolved_proof_of_work)

            resolved = "%s%d" % (self.proof_of_work['question'], int_pow)
            x = sha256(bytes(resolved))
            if not x.endswith(HASH_ENDS_WITH):
                log.debug("Failed proof of work validation: expected '%s' at the end of the hash %s (seeds %s + %d)" %
                          (HASH_ENDS_WITH, x, self.proof_of_work['question'], int_pow))
                return True

            log.debug("Successful proof of work validation! got '%s' at the end of the hash %s (seeds %s + %d)" %
                      (HASH_ENDS_WITH, x, self.proof_of_work['question'], int_pow))

            # mark the proof_of_work as solved
            self.proof_of_work = False

            return False
        except Exception as e:
            log.debug("Exception while validating the proof of work: %s" % e)
            return True

    def validity_checks(self):
        self.timedelta_check()

        if self.remaining_uses <= 0:
            raise errors.TokenFailure("Token is no more valid.")

    def update(self, request):
        error = False

        if self.human_captcha is not False:
            if 'human_captcha_answer' in request:
                error |= self.human_captcha_check(request['human_captcha_answer'])
            else:
                error = True

        if not error and self.graph_captcha is not False:
            raise errors.TokenFailure("Graphical captcha error: not yet implemented")

        if not error and self.proof_of_work is not False:
            if 'proof_of_work_answer' in request:
                error |= self.proof_of_work_check(request['proof_of_work_answer'])
            else:
                error = True

        if error:
            # change questions!
            self.generate_token_challenge()

        return error

    def use(self):
        self.validity_checks()

        if self.human_captcha is not False or \
           self.graph_captcha is not False or \
           self.proof_of_work is not False:
             raise errors.TokenFailure("Token still requires user action to be used.")

        self.remaining_uses -= 1
        if self.remaining_uses <= 0:
            del TokenList[self.id]
