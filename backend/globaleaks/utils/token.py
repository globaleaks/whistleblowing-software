# -*- coding: UTF-8
#
#   token
#   *****
#
#   Implements a GlobaLeaks security token, to prevent resources exhaustion
#   operation by anonymous user in a serial approach.

from random import randint
from datetime import datetime, timedelta

from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601
from globaleaks.third_party import rstr
from globaleaks.rest import errors
from globaleaks.utils.tempobj import TempObj

# from Captcha.Visual.Tests import PseudoGimpy
from StringIO import StringIO
import base64


class TokenList:

    token_dict = dict()

    @staticmethod
    def del_Token(t_id):
        """
        Token can be used only once, so need to be remove after the first usage.
        :param t_id:
        :return:
        """
        if not TokenList.token_dict.has_key(t_id):
            raise errors.TokenRequestError("Not found")

        del TokenList.token_dict[t_id]

    @staticmethod
    def get(t_id):
        if not TokenList.token_dict.has_key(t_id):
            raise errors.TokenRequestError("Not found")

        return TokenList.token_dict[t_id]

    @staticmethod
    def validate_token_id(unclean_token_id):
        """
        Format:
        token_id+humancaptchaanswer+graphcaptchanaser+hashcash
        is used split over the symbol "+"
        the token can be in two shape:
            only the token
            only the token+[optional]+[optional]+[optional]
        """
        plus_number = unclean_token_id.count('-')
        if plus_number != 0 and plus_number != 3:
            raise errors.TokenRequestError("Format error: #N of +'s: 0 or 3")

        retdict = {
            'token_object' : None,
            'g_captcha' : None,
            'h_captcha' : None,
            'hashcash' : None
        }

        if plus_number == 3:
            answers = unclean_token_id.split('-')
            retdict['token_object'] = TokenList.get(answers[0])
            retdict['g_captcha'] = answers[1]
            retdict['h_captcha'] = answers[2]
            retdict['hashcash'] = answers[3]
        else:
            retdict['token_object'] = TokenList.get(unclean_token_id)
            # the other fields remain None, and if they are needed, the selective
            # validation simply fail

        return retdict

# needed in order to allow UT override
reactor = None

class Token(TempObj):

    existing_kind = ['upload', 'submission']
    SUBMISSION_MINIMUM_DELAY = 60
    UPLOAD_MINIMUM_DELAY = 5
    MAXIMUM_AVAILABILITY = 4 * 60
    MAXIMUM_USAGES_FILEUPLOAD = 10

    def __init__(self, token_kind, debug=False):
        """
        token_kind is 'file' or 'submission' right now, will be
            enhanced in typology later. is used an Assertion below.
        debug = I totally love verbose debugging when we can used it :P
        """
        assert token_kind in Token.existing_kind, "unsupported kind: %s" % token_kind
        self.kind = token_kind

        self.debug = debug
        # both 'validity' need to be expressed in seconds
        self.end_validity = Token.MAXIMUM_AVAILABILITY

        if self.kind == 'submission':
            self.start_validity = Token.SUBMISSION_MINIMUM_DELAY
            self.usages = 1
        else:
            self.start_validity = Token.UPLOAD_MINIMUM_DELAY
            self.usages = Token.MAXIMUM_USAGES_FILEUPLOAD

        # creation_date of the borning
        self.creation_date = datetime.utcnow()

        self.token_id = rstr.xeger(r'[A-Za-z0-9]{42}')

        TempObj.__init__(self,
                         TokenList.token_dict,
                         # token ID:
                         self.token_id,
                         # seconds of validity:
                         self.start_validity + self.end_validity,
                         reactor)

    def touch(self):
        assert False, "touch() is disabled for Token, their validity cannot be postponed"

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

        # .set_difficulty is needed to take a Token
        assert hasattr(self, 'graph_captcha' ), "call .set_difficulty()"
        return {
            'token_id' : self.token_id,
            'creation_date' : datetime_to_ISO8601(self.creation_date),
            'start_validity': datetime_to_ISO8601(self.creation_date +
                                                  timedelta(seconds=self.start_validity) ),
            'end_validity': datetime_to_ISO8601(self.creation_date +
                                                timedelta(seconds=self.end_validity) ),
            'usages': self.usages,
            'type': self.kind,
            'g_captcha': self.graph_captcha['question'] if self.graph_captcha else False,
            'h_captcha': self.human_captcha['question'] if self.human_captcha else False,
            'hashcash': self.proof_of_work['question'] if self.proof_of_work else False,
        }

    def set_difficulty(self, problems_dict):
        """
        @problems_dict: arrive directly from anomaly.Alarm.get_token_difficulty
            and in a future enhancement we can implement set_difficult in
            FileToken or SubmissionToken and here the shared element.
        """

        self.human_captcha = None
        if problems_dict['human_captcha']:
            random_a = randint(1, 10)
            random_b = randint(1, 10)

            self.human_captcha = {
                'question': u"%d + %d" % (random_a, random_b),
                'answer' : u"%d" % (random_a + random_b)
            }

        self.proof_of_work = None
        # TODO

        self.graph_captcha = None
        if problems_dict['graph_captcha']:
            """
            g = PseudoGimpy()
            i = g.render()
            tmpf = StringIO()

            i.save(tmpf, 'png')
            tmpf.seek(0)
            request = unicode( "datauri://%s" % base64.b64encode(tmpf.read()))

            self.graph_captcha = {
                'question' : request,
                'answer' : g.solutions,
            }
            """
            print "suca ATM"

        if problems_dict['graph_captcha'] and self.kind == 'upload':
            self.usages /= 2



    def timedelta_check(self):
        """
        This timedelta check verify that the current time fit between
        the starting_

        """
        now = datetime_now()
        start = (self.creation_date + timedelta(seconds=self.start_validity) )
        if not start < now:
            raise errors.TokenRequestError("Too early to use this token")


        # This will never raises when I've integrated the self expising
        # object.
        end = (self.creation_date + timedelta(self.end_validity) )
        if now > end:
            raise errors.TokenRequestError("Too late to use this token")

        # If the code reach here, the time delta is good.


    def human_captcha_check(self, resolved_human_captcha):
        """
        Check the human captcha with the pseudo-mockup we're right now
        """
        if not self.human_captcha:
            return

        if self.human_captcha['answer'] != resolved_human_captcha:
            log.debug("Failed Human captcha: expected %s got %s" % (
                self.human_captcha['answer'], resolved_human_captcha
            ))
            raise errors.TokenRequestError("Failed Human captcha")
        else:
            log.debug("Successful Human captcha resolution: %s" %
                      resolved_human_captcha)

    def graph_captcha_check(self, resolved_graph_captcha):

        if not self.graph_captcha:
            return

        if self.graph_captcha['answer'] != resolved_graph_captcha:
            log.debug("Failed Graph captcha: expected %s got %s" % (
                self.graph_captcha['answer'], resolved_graph_captcha
            ))
            raise errors.TokenRequestError("Failed Graphical captcha")
        else:
            log.debug("Successfil Graphical captcha resolution: %s" %
                      resolved_graph_captcha)


    def hashcash_check(self, resolved_hashcash):
        pass


    def validate(self, submitted_entities):
        """
        @submitted_entities is a dict, this is the default values: {
            'token_object' : None,
            'g_captcha' : None,
            'h_captcha' : None,
            'hashcash' : None
        }

        """
        # any of these can raise an exception if check fail

        self.timedelta_check()
        self.human_captcha_check(submitted_entities['h_captcha'])
        self.graph_captcha_check(submitted_entities['g_captcha'])
        self.hashcash_check(submitted_entities['hashcash'])

        # if the code flow reach here, the token is validated
        log.debug("Token validated properly")




