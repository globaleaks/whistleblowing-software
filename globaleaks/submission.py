# -*- coding: UTF-8
#   submission
#   **********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Implements a GlobaLeaks submission.

from twisted.internet.defer import returnValue, inlineCallbacks
from globaleaks.db import models, transactor
from globaleaks.db import transact
from globaleaks.utils.random import random_string

"""
Move this utility in globaleaks.utils.random or globaleaks.utils.id ?
remind: ID need to be unique, and may support a prefix
"""
def random_submission_id():
    import random
    import string
    length = 50
    return ''.join(random.choice(string.ascii_letters) for x in range(length))

def random_receipt_id():
    import random
    import string
    length = 10
    return ''.join(random.choice('0123456789') for x in range(length))

class Submission:
    handler = None
    model = models.Submission()
    transactor = transactor

    def new(self, *arg, **kw):
        """
        Creates an empty submission and returns the ID to the WB.
        """
        self.handler.status_code = 201
        return {'submission_id': random_submission_id()}

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

    def files(self, submission_id, *arg, **kw):
        """
        Adds the material to the specified submission id.

        :material: append the material to the material set
        """
        return {'submission_id': submission_id}

    def fields(self, submission_id, fields=None, *arg, **kw):
        """
        Add the fields to the submission.

        :fields: a dict containing the submitted fields
        """
        print "Fields: %s" % fields
        return {'submission_id': submission_id}

    def groups(self, submission_id, *arg, **kw):
        """
        Adds the group to the list of groups.

        :group: the group to be appendend to the group array.
        """
        return {'submission_id': submission_id}

    @inlineCallbacks
    def finalize(self, submission_id, **form_fields):
        """
        Finalize the submission and create data inside of the database.
        """
        receipt_id = unicode(random_receipt_id())
        self.handler.status_code = 201
        internal_tip = models.InternalTip()
        internal_tip.fields = form_fields

        yield internal_tip.save()

        whistleblower_tip = models.Tip()
        whistleblower_tip.internaltip_id = internal_tip.id
        whistleblower_tip.address = receipt_id

        yield whistleblower_tip.save()

        returnValue({'receipt': receipt_id})

