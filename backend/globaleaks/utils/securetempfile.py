# -*- coding: utf-8 -*-
import base64
import json
import os
import tempfile
import time

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.utils.security import crypto_backend, generateRandomKey
from globaleaks.utils.utility import log


class SecureTemporaryFile(tempfile._TemporaryFileWrapper):
    """
    WARNING!
    You can't use this File object like a normal file object,
    check .read and .write!
    """
    last_action = 'init'
    finalize_called = False

    def __init__(self, filedir):
        """
        filedir: directory where to store files
        """
        self.creation_date = time.time()

        self.create_key()
        self.encryptor_finalized = False

        # XXX remind enhance file name with incremental number
        self.filepath = os.path.join(filedir, "%s.aes" % self.key_id)

        log.debug("++ Creating %s filetmp", self.filepath)

        self.file = open(self.filepath, 'w+b')

        # last argument is 'True' because the file has to be deleted on .close()
        tempfile._TemporaryFileWrapper.__init__(self, self.file, self.filepath, True)

    def initialize_cipher(self):
        self.cipher = Cipher(algorithms.AES(self.key), modes.CTR(self.key_counter_nonce), backend=crypto_backend)
        self.encryptor = self.cipher.encryptor()
        self.decryptor = self.cipher.decryptor()

    def init_read(self):
        self.last_action = 'read'
        self.seek(0, 0)  # this is a trick just to misc write and read
        self.initialize_cipher()
        log.debug("First seek on %s", self.filepath)

    def create_key(self):
        """
        Create the AES Key to encrypt uploaded file.
        """
        self.key = os.urandom(Settings.AES_key_size)

        self.key_id = generateRandomKey(16)
        self.keypath = os.path.join(Settings.ramdisk_path, "%s%s" %
                                    (Settings.AES_keyfile_prefix, self.key_id))

        while os.path.isfile(self.keypath):
            self.key_id = generateRandomKey(16)
            self.keypath = os.path.join(Settings.ramdisk_path, "%s%s" %
                                        (Settings.AES_keyfile_prefix, self.key_id))

        self.key_counter_nonce = os.urandom(Settings.AES_counter_nonce)
        self.initialize_cipher()

        key_json = {
            'key': base64.b64encode(self.key),
            'key_counter_nonce': base64.b64encode(self.key_counter_nonce)
        }

        log.debug("Key initialization at %s", self.keypath)

        with open(self.keypath, 'w') as kf:
            json.dump(key_json, kf)

        if not os.path.isfile(self.keypath):
            log.err("Unable to write keyfile %s", self.keypath)
            raise Exception("Unable to write keyfile %s" % self.keypath)

    def avoid_delete(self):
        log.debug("Avoid delete on: %s", self.filepath)
        self.delete = False

    def write(self, data):
        """
        The last action is kept track because the internal status
        need to track them. read below read()
        """
        if self.last_action == 'read':
            raise Exception("Error: Write call performed after read")

        self.last_action = 'write'
        if isinstance(data, unicode):
            data = data.encode('utf-8')

        self.file.write(self.encryptor.update(data))

    def finalize(self):
        if not self.finalize_called:
            self.finalize_called = True

            try:
                if any(x in self.file.mode for x in 'wa') and not self.encryptor_finalized:
                    self.encryptor_finalized = True
                    self.file.write(self.encryptor.finalize())
            except:
                pass


    def close(self):
        if not self.close_called:
            self.finalize()

            try:
                if self.delete:
                    pass#overwrite_and_remove(self.keypath)
            except:
                pass

        try:
            tempfile._TemporaryFileWrapper.close(self)
        except:
            pass

    def read(self, c=None):
        """
        The first time 'read' is called after a write, seek(0) is performed
        """
        if self.last_action == 'write':
            self.finalize()

        if self.last_action != 'read':
            self.init_read()

        if c is None:
            data = self.file.read()
        else:
            data = self.file.read(c)

        if data:
            return self.decryptor.update(data)

        return self.decryptor.finalize()


class SecureFile(SecureTemporaryFile):
    def __init__(self, filepath):
        self.filepath = filepath

        self.key_id = os.path.basename(self.filepath).split('.')[0]

        log.debug("Opening secure file %s with %s", self.filepath, self.key_id)

        self.file = open(self.filepath, 'r+b')

        # last argument is 'False' because the file has not to be deleted on .close()
        tempfile._TemporaryFileWrapper.__init__(self, self.file, self.filepath, False) # pylint: disable=W0233

        self.load_key()

    def load_key(self):
        """
        Load the AES Key to decrypt uploaded file.
        """
        self.keypath = os.path.join(Settings.ramdisk_path, ("%s%s" % (Settings.AES_keyfile_prefix, self.key_id)))

        try:
            with open(self.keypath, 'r') as kf:
                key_json = json.load(kf)

            self.key = base64.b64decode(key_json['key'])
            self.key_counter_nonce = base64.b64decode(key_json['key_counter_nonce'])
            self.initialize_cipher()

        except Exception as excep:
            log.err("The file %s has been encrypted with a lost/invalid key (%s)", self.keypath, excep.message)
            raise
