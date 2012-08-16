"""
    Submission
    **********

    Implements a GlobaLeaks submission.
"""
import random
import string

from globaleaks.utils.random import random_string

class Submission:
    rest = None
    def new(self, *arg, **kw):
        return {'submission_id': 12345}

    def files(self, submission_id, *arg, **kw):
        """
        Adds the material to the specified submission id.

        :material: append the material to the material set
        """
        return {'submission_id': submission_id}

    def fields(self, submission_id, *arg, **kw):
        """
        Add the fields to the submission.

        :fields: a dict containing the submitted fields
        """
        return {'submission_id': submission_id}

    def groups(self, submission_id, *arg, **kw):
        """
        Adds the group to the list of groups.

        :group: the group to be appendend to the group array.
        """
        return {'submission_id': submission_id}

    def finalize(self, submission_id, *arg, **kw):
        """
        Finalize the submission and create data inside of the database.
        """
        return {'submission_id': submission_id}

    def status(self, submission_id, *arg, **kw):
        from datetime import datetime
        status_dict = { 'fields': {'foo': 1234},
                        'groups': ['A', 'B'],
                        'files': [{'name': 'fileA', 'location': '/tmp/foo', 'percent': 100},
                                 {'name': 'fileB', 'location': '/tmp/foo', 'percent': 100},
                                 {'name': 'fileC', 'location': '/tmp/foo', 'percent': 100}],
                        'creation_time': str(datetime.now())
                      }
        return status_dict


