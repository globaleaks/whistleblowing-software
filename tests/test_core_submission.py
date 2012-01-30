import unittest

from globaleaks.core import submission

# Shift to a new database adhibit for testing
submission._dbpath = 'testsubmission.db'

class TestSubmission(unittest.TestCase):
    """
    Performs various tests on submissions, especially:
        - malicious code injection
        - stress
    """

    def setUp(self):
        """
        Create a new Submission in the database.
        """
        self.sid = '00666'
        # self.sub

    def test_new(self):
        """
        Test a valid submission instance is returned only if the sid is correct.
        """
        self.assertIsNone(submission.Submission('0000'))


