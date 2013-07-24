# -*- coding: UTF-8
#
#   gpgexpire_sched
#   ***************
#
# Implements a periodic checks to verify if keys configured by receiver are going
# to expire in short time, if so, send a warning email to the recipient.
# It's execute once per day.
import os
import sys

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.models import InternalFile, InternalTip, ReceiverTip,\
    ReceiverFile, Receiver
from globaleaks.settings import transact, GLSetting
from globaleaks.utils import get_file_checksum, log, pretty_date_time
from globaleaks.security import get_expirations
from globaleaks.handlers.admin import admin_serialize_receiver

__all__ = ['GPGExpireCheck']

@transact
def check_expiration_date(store):

    all_rcvs = store.find(Receiver)

    keylist = []
    keytrack = {}

    for sr in all_rcvs:
        if sr.gpg_key_status == Receiver._gpg_types[1]: # Enabled
            keylist.append(sr.gpg_key_armor)

            if keytrack.has_key(sr.gpg_key_fingerprint):
                print "umh, duplicated key fingerprint between %s and %s" %\
                      (sr.username, keytrack[sr.gpg_key_fingerprint])

            keytrack.update({sr.gpg_key_fingerprint : sr.username })

    dates = get_expirations(keylist)

    print dates

def GPGEXpireCheck(GLJob):

    @inlineCallbacks
    def operation(self):

        (two_weeks, three_days, gone) = yield self.check_expiration_date()


