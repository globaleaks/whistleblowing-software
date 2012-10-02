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

    @classmethod
    def timecheckf(self, value):
        return True

    @classmethod
    def boolcheckf(self, value):
        return True

    """
    regexp (\w+) with a size limit
    """
    @classmethod
    def stringcheckf(self, value):
        return True

    @classmethod
    def intcheckf(self, value):
        return True

    """
    Every ID has a different format, they have the first
    letter recalling the meaning of the ID, in example:

    tip with "t_"
    context start with "c_", 
    module with "m_"
    receiver with "r_"
    session with "s_" 

    for be easily recognezed by human eye 
    """
    @classmethod
    def tipIDcheckf(self, value):
        return idops.regexp_tip_id(value)
    @classmethod
    def contextIDcheckf(self, value):
        return idops.regexp_context_id(value)
    @classmethod
    def moduleIDcheckf(self, value):
        return idops.regexp_module_id(value)
    @classmethod
    def receiverIDcheckf(self, value):
        return idops.regexp_receiver_id(value)
    @classmethod
    def sessionIDcheckf(self, value):
        return idops.regexp_submission_id(value)
    @classmethod
    def folderIDcheckf(self, value):
        return idops.regexp_folder_id(value)

    """
    receipt format, default 10 digits, its a configurable format
    """
    @classmethod
    def receiptIDcheckf(self, value):
        return idops.regexp_receipt_id(value)



    """
    ("your"|"external"|"whistleblower")
    """
    @classmethod
    def commentENUMcheckf(self, value):
        return True

    """
    ("notification"|"delivery"|"inputfilter"|"dbstorage")
    """
    @classmethod
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

    @classmethod
    def booldeflt(self):
        return False

    @classmethod
    def stringdeflt(self):
        return 'defaultWRONGstring'

    @classmethod
    def intdeflt(self):
        return 12345678

    @classmethod
    def moduleIDdeflt(self):
        return idops.random_module_id()

    @classmethod
    def contextIDdeflt(self):
        return idops.random_context_id()

    @classmethod
    def tipIDdeflt(self):
        return idops.random_tip_id()

    @classmethod
    def receiverIDdeflt(self):
        return idops.random_receiver_id()

    @classmethod
    def sessionIDdeflt(self):
        return idops.random_submission_id()

    @classmethod
    def folderIDdeflt(self):
        return idops.random_folder_id()

    @classmethod
    def commentENUMdeflt(self):
        return 'comment_ENUM_UNSET'

    @classmethod
    def moduleENUMdeflt(self):
        return 'module_ENUM_UNSET'

    @classmethod
    def timedeflt(self):
        return datetime.datetime.ctime(datetime.datetime.today())
        # yay, it's shit

