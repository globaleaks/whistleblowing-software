# -*- coding: utf-8 -*-
import os
import shutil
import tempfile

from datetime import datetime

from gnupg import GPG

from globaleaks.rest import errors
from globaleaks.utils.utility import log


class PGPContext(object):
    """
    PGP does not have a dedicated class, because one of the function is called inside a transact.
    I'm not confident creating an object that operates on the filesystem knowing that
    would be run also on the Storm cycle.
    """
    def __init__(self, tempdirprefix=None):
        """
        every time is needed, a new keyring is created here.
        """
        if tempdirprefix is None:
            tempdir = tempfile.mkdtemp()
        else:
            tempdir = tempfile.mkdtemp(prefix=tempdirprefix)

        try:
            gpgbinary='gpg'
            if os.path.exists('/usr/bin/gpg1'):
                gpgbinary='gpg1'

            self.gnupg = GPG(gpgbinary=gpgbinary, gnupghome=tempdir, options=['--trust-model', 'always'])
            self.gnupg.encoding = "UTF-8"
        except OSError as excep:
            log.err("Critical, OS error in operating with GnuPG home: %s", excep)
            raise
        except Exception as excep:
            log.err("Unable to instance PGP object: %s" % excep)
            raise

    def load_key(self, key):
        """
        @param key
        @return: a dict with the expiration date and the key fingerprint
        """
        try:
            import_result = self.gnupg.import_keys(key)
        except Exception as excep:
            log.err("Error in PGP import_keys: %s", excep)
            raise errors.InputValidationError

        if not import_result.fingerprints:
            raise errors.InputValidationError

        fingerprint = import_result.fingerprints[0]

        # looking if the key is effectively reachable
        try:
            all_keys = self.gnupg.list_keys()
        except Exception as excep:
            log.err("Error in PGP list_keys: %s", excep)
            raise errors.InputValidationError

        expiration = datetime.utcfromtimestamp(0)
        for k in all_keys:
            if k['fingerprint'] == fingerprint:
                if k['expires']:
                    expiration = datetime.utcfromtimestamp(int(k['expires']))
                break

        return {
            'fingerprint': fingerprint,
            'expiration': expiration
        }

    def encrypt_file(self, key_fingerprint, input_file, output_path):
        """
        Encrypt a file with the specified PGP key
        """
        encrypted_obj = self.gnupg.encrypt_file(input_file, str(key_fingerprint), output=output_path)

        if not encrypted_obj.ok:
            raise errors.InputValidationError

        return encrypted_obj,  os.stat(output_path).st_size

    def encrypt_message(self, key_fingerprint, plaintext):
        """
        Encrypt a text message with the specified key
        """
        encrypted_obj = self.gnupg.encrypt(plaintext, str(key_fingerprint))

        if not encrypted_obj.ok:
            raise errors.InputValidationError

        return str(encrypted_obj)

    def __del__(self):
        try:
            shutil.rmtree(self.gnupg.gnupghome)
        except Exception as excep:
            log.err("Unable to clean temporary PGP environment: %s: %s", self.gnupg.gnupghome, excep)
