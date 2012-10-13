import json
from twisted.trial import unittest

from globaleaks.messages import validateMessage, validateWith
from globaleaks.messages.base import *
from globaleaks.messages.errors import *
from globaleaks.messages.dummy import *

from cyclone.util import ObjectDict

class TestMessages(unittest.TestCase):

    def setUp(self):
        self.request = ObjectDict()
        self.request.body = base.fileDicts[0].copy()

    def test_file_dict(self):
        test_fd = base.fileDicts[0].copy()

        message = json.dumps(test_fd)
        validateMessage(message, fileDict)

        test_fd['size'] = "not-valid"
        message = json.dumps(test_fd)
        self.failUnlessRaises(GLTypeError, validateMessage, message, fileDict)

    def test_folder_dict(self):
        message = json.dumps(base.folderDict)
        validateMessage(message, folderDict)

    def test_invalid_folder_dict(self):
        invalid_fd = base.folderDict.copy()
        invalid_fd['files'] = 'sux'
        message = json.dumps(invalid_fd)
        self.failUnlessRaises(GLTypeError, validateMessage, message,
                folderDict)

    def test_receiver_dict(self):
        message = json.dumps(base.receiverDescriptionDicts[0])
        validateMessage(message, receiverDescriptionDict)

    def test_invalid_receiver_dict(self):
        invalid_rd = base.receiverDescriptionDicts[0].copy()
        invalid_rd["language_supported"] = 'sux'
        message = json.dumps(invalid_rd)
        self.failUnlessRaises(GLTypeError, validateMessage, message,
                receiverDescriptionDict)

    def test_invalid_special_field(self):
        invalid_rd = base.receiverDescriptionDicts[0].copy()
        invalid_rd["rID"] = 'sux'
        message = json.dumps(invalid_rd)
        self.failUnlessRaises(GLTypeError, validateMessage, message,
                receiverDescriptionDict)

    def test_admin_statistics(self):
        message = json.dumps(base.adminStatisticsDict)
        validateMessage(message, adminStatisticsDict)

    def test_validator_decorator(self):
        pass

