# -*- coding: UTF-8
#   tip
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Contains all the logic for handling tip related operations.

# ------
# remind: raise TypeError

import datetime
from globaleaks.utils import idops

class validatorRegExps:

    @staticmethod
    def timecheckf(self, value):
        return True

    @staticmethod
    def boolcheckf(self, value):
        return True

    """
    regexp (\w+) with a size limit
    """
    @staticmethod
    def stringcheckf(self, value):
        return True

    @staticmethod
    def intcheckf(self, value):
        return True

    """
    Every ID has a different format, they have the first
    letter recalling the meaning of the ID, in example:

    tip with "t_"
    context start with "c_",
    module with "m_"
    receiver with "r_"
    submission with "s_"

    for be easily recognezed by human eye
    """
    @staticmethod
    def tipIDcheckf(self, value):
        return idops.regexp_tip_id(value)
    @staticmethod
    def contextIDcheckf(self, value):
        return idops.regexp_context_id(value)
    @staticmethod
    def moduleIDcheckf(self, value):
        return idops.regexp_module_id(value)
    @staticmethod
    def receiverIDcheckf(self, value):
        return idops.regexp_receiver_id(value)
    @staticmethod
    def submissionIDcheckf(self, value):
        return idops.regexp_submission_id(value)
    @staticmethod
    def folderIDcheckf(self, value):
        return idops.regexp_folder_id(value)

    """
    receipt format, default 10 digits, its a configurable format
    """
    @staticmethod
    def receiptIDcheckf(self, value):
        return idops.regexp_receipt_id(value)


    """
    ("your"|"external"|"whistleblower")
    """
    @staticmethod
    def commentENUMcheckf(self, value):
        return True

    """
    ("notification"|"delivery"|"inputfilter"|"dbstorage")
    """
    @staticmethod
    def moduleENUMcheckf(self, value):
        return True


"""
default values, are used with a content that permit
no mistake, because need to be immediately understandable,
if some value is present without initialization/assignment.
Exception made for bool :(
"""
class defltvals:

    IDcounter = 0

    @staticmethod
    def booldeflt(self):
        return False

    @staticmethod
    def stringdeflt(self):
        return 'defaultWRONGstring'

    @staticmethod
    def intdeflt(self):
        return 12345678

    @staticmethod
    def moduleIDdeflt(self):
        return idops.random_module_id()

    @staticmethod
    def contextIDdeflt(self):
        return idops.random_context_id()

    @staticmethod
    def tipIDdeflt(self):
        return idops.random_tip_id()

    @staticmethod
    def receiptIDdeflt(self):
        return idops.random_receipt_id()

    @staticmethod
    def receiverIDdeflt(self):
        return idops.random_receiver_id()

    @staticmethod
    def submissionIDdeflt(self):
        return idops.random_submission_id()

    @staticmethod
    def folderIDdeflt(self):
        return idops.random_folder_id()

    @staticmethod
    def commentENUMdeflt(self):
        return 'comment_ENUM_UNSET'

    @staticmethod
    def moduleENUMdeflt(self):
        return 'module_ENUM_UNSET'

    @staticmethod
    def timedeflt(self):
        return datetime.datetime.ctime(datetime.datetime.today())
        # yay, it's shit

