import json
from twisted.trial import unittest

from globaleaks.rest.messages.base import *
from globaleaks.rest.messages.errors import *

dummy_file_dict = {"filename": 'hello',
    "file_description": 'world',
    "size": 10,
    "content_type": 'hello',
    "date": '123123321312',
    "cleaned_meta_data": True,
    "completed": False
}

dummy_receiver_dict = {"rID": "dummy",
            "can_delete_submission": True,
            "can_postpone_expiration": True,
            "can_configure_notification": True,
            "can_configure_delivery": True,
            # -----------------------------------------
            "can_trigger_escalation": True,
            "receiver_level": 1,
            # remind: both of them need to be specified
            "receiver_name": 'foobar',
            "receiver_description": 'foobar',
            "receiver_tags": 'foobar',
            # verify - is it specified ?
            "creation_date": '123241',
            "last_update_date": 'e21',
            # update the name
            "language_supported": ['a', 'b']
            }

dummy_folder_dict = {"fID": '12341231',
         "folder_name": 'foobar',
         "folder_description": 'world',
         "download_performed": 10,
         "files": [dummy_file_dict, dummy_file_dict]}

class TestMessages(unittest.TestCase):

    def test_file_dict(self):
        test_fd = dummy_file_dict.copy()

        message = json.dumps(test_fd)
        validateMessage(message, fileDict)

        test_fd['size'] = "not-valid"
        message = json.dumps(test_fd)
        self.failUnlessRaises(GLTypeError, validateMessage, message, fileDict)

    def test_folder_dict(self):
        message = json.dumps(dummy_folder_dict)
        validateMessage(message, folderDict)

    def test_invalid_folder_dict(self):
        invalid_fd = dummy_folder_dict.copy()
        invalid_fd['files'] = 'sux'
        message = json.dumps(invalid_fd)
        self.failUnlessRaises(Exception, validateMessage, message,
                folderDict)

    def test_receiver_dict(self):
        message = json.dumps(dummy_receiver_dict)
        validateMessage(message, receiverDescriptionDict)

    def test_invalid_receiver_dict(self):
        invalid_rd = dummy_receiver_dict.copy()
        invalid_rd["language_supported"] = 'sux'
        message = json.dumps(invalid_rd)
        self.failUnlessRaises(GLTypeError, validateMessage, message,
                receiverDescriptionDict)
