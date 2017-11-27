# -*- coding: utf-8 -*-
#
# security
# ********
#
# GlobaLeaks security functions

import base64
import binascii
import json
import os
import random
import scrypt
import shutil
import string
import tempfile
import time
from datetime import datetime
from gnupg import GPG

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import constant_time, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.utils.utility import log

crypto_backend = default_backend()

def sha256(data):
    h = hashes.Hash(hashes.SHA256(), backend=crypto_backend)
    h.update(data)
    return binascii.b2a_hex(h.finalize())


def sha512(data):
    h = hashes.Hash(hashes.SHA512(), backend=crypto_backend)
    h.update(data)
    return binascii.b2a_hex(h.finalize())


def generateRandomReceipt():
    """
    Return a random receipt of 16 digits
    """
    return ''.join(random.SystemRandom().choice(string.digits) for _ in range(16)).encode('utf-8')


def generateRandomKey(N):
    """
    Return a random key of N characters in a-zA-Z0-9
    """
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(N)).encode('utf-8')


def generateRandomSalt():
    """
    Return a base64 encoded string with 128 bit of entropy
    """
    return base64.b64encode(os.urandom(16))


def generate_api_token():
    """
    creates an api token along with its corresponding hash digest.

    :rtype: A `tuple` containing (digest `str`, token `str`)
    """
    token = generateRandomKey(Settings.api_token_len)
    token_hash = sha512(token)
    return token, token_hash


def _overwrite(absolutefpath, pattern):
    count = 0
    length = len(pattern)

    with open(absolutefpath, 'w+') as f:
        f.seek(0)
        while count < length:
            f.write(pattern)
            count += len(pattern)


def overwrite_and_remove(absolutefpath, iterations_number=1):
    """
    Overwrite the file with all_zeros, all_ones, random patterns

    Note: At each iteration the original size of the file is altered.
    """
    log.debug("Starting secure deletion of file %s", absolutefpath)

    randomgen = random.SystemRandom()

    try:
        # in the following loop, the file is open and closed on purpose, to trigger flush operations
        all_zeros = "\0\0\0\0" * 1024               # 4kb of zeros
        all_ones = "FFFFFFFF".decode("hex") * 1024  # 4kb of ones

        for iteration in range(iterations_number):
            OPTIMIZATION_RANDOM_BLOCK = randomgen.randint(4096, 4096 * 2)

            random_pattern = ""
            for _ in range(OPTIMIZATION_RANDOM_BLOCK):
                random_pattern += str(randomgen.randrange(256))

            log.debug("Excecuting rewrite iteration (%d out of %d)",
                      iteration, iterations_number)

            _overwrite(absolutefpath, all_zeros)
            _overwrite(absolutefpath, all_ones)
            _overwrite(absolutefpath, random_pattern)

    except Exception as excep:
        log.err("Unable to perform secure overwrite for file %s: %s",
                absolutefpath, excep)

    finally:
        try:
            os.remove(absolutefpath)
        except OSError as excep:
            log.err("Unable to perform unlink operation on file %s: %s",
                    absolutefpath, excep)

    log.debug("Performed deletion of file: %s", absolutefpath)


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
                    overwrite_and_remove(self.keypath)
            except:
                pass

        try:
            tempfile._TemporaryFileWrapper.close(self)
        except Exception:
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
            # I'm sorry, that file is a dead file!
            log.err("The file %s has been encrypted with a lost/invalid key (%s)", self.keypath, excep.message)
            raise


def directory_traversal_check(trusted_absolute_prefix, untrusted_path):
    """
    check that an 'untrusted_path' matches a 'trusted_absolute_path' prefix
    """
    if not os.path.isabs(trusted_absolute_prefix):
        raise Exception("programming error: trusted_absolute_prefix is not an absolute path: %s" %
                        trusted_absolute_prefix)

    untrusted_path = os.path.abspath(untrusted_path)

    if trusted_absolute_prefix != os.path.commonprefix([trusted_absolute_prefix, untrusted_path]):
        log.err("Blocked file operation for: (prefix, attempted_path) : ('%s', '%s')",
                trusted_absolute_prefix, untrusted_path)

        raise errors.DirectoryTraversalError


def hash_password(password, salt):
    """
    @param password: a unicode or utf-8 string
    @param salt: a password salt

    @return:
        the salted scrypt hash of the provided password
    """
    password = password.encode('utf-8')
    salt = salt.encode('utf-8')
    return scrypt.hash(password, salt).encode('hex')


def check_password(guessed_password, salt, password_hash):
    return constant_time.bytes_eq(hash_password(guessed_password, salt), bytes(password_hash))


def change_password(old_password_hash, old_password, new_password, salt):
    """
    @param old_password_hash: the stored password hash.
    @param old_password: The user provided old password for password change protection.
    @param new_password: The user provided new password.
    @param salt: The salt to be used for password hashing.

    @return:
        the scrypt hash in base64 of the new password
    """
    if not check_password(old_password, salt, old_password_hash):
        log.debug("change_password(): Error - provided invalid old_password")
        raise errors.InvalidOldPassword

    return hash_password(new_password, salt)


class GLBPGP(object):
    """
    PGP does not have a dedicated class, because one of the function is called inside a transact.
    I'm not confident creating an object that operates on the filesystem knowing that
    would be run also on the Storm cycle.
    """
    def __init__(self):
        """
        every time is needed, a new keyring is created here.
        """
        try:
            self.gnupg = GPG(gnupghome=tempfile.mkdtemp(), options=['--trust-model', 'always'])
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
            raise errors.PGPKeyInvalid

        if not import_result.fingerprints:
            raise errors.PGPKeyInvalid

        fingerprint = import_result.fingerprints[0]

        # looking if the key is effectively reachable
        try:
            all_keys = self.gnupg.list_keys()
        except Exception as excep:
            log.err("Error in PGP list_keys: %s", excep)
            raise errors.PGPKeyInvalid

        expiration = datetime.utcfromtimestamp(0)
        for k in all_keys:
            if k['fingerprint'] == fingerprint:
                if k['expires']:
                    expiration = datetime.utcfromtimestamp(int(k['expires']))
                break

        return {
            'fingerprint': fingerprint,
            'expiration': expiration,
        }

    def encrypt_file(self, key_fingerprint, input_file, output_path):
        """
        Encrypt a file with the specified PGP key
        """
        encrypted_obj = self.gnupg.encrypt_file(input_file, str(key_fingerprint), output=output_path)

        if not encrypted_obj.ok:
            raise errors.PGPKeyInvalid

        return encrypted_obj,  os.stat(output_path).st_size

    def encrypt_message(self, key_fingerprint, plaintext):
        """
        Encrypt a text message with the specified key
        """
        encrypted_obj = self.gnupg.encrypt(plaintext, str(key_fingerprint))

        if not encrypted_obj.ok:
            raise errors.PGPKeyInvalid

        return str(encrypted_obj)

    def destroy_environment(self):
        try:
            shutil.rmtree(self.gnupg.gnupghome)
        except Exception as excep:
            log.err("Unable to clean temporary PGP environment: %s: %s", self.gnupg.gnupghome, excep)


def encrypt_message(pgp_key_public, msg):
    gpob = GLBPGP()

    try:
        fingerprint = gpob.load_key(pgp_key_public)['fingerprint']
        body = gpob.encrypt_message(fingerprint, msg)
    except Exception:
        raise
    finally:
        gpob.destroy_environment()

    return body


def parse_pgp_key(key):
    """
    Used for parsing a PGP key

    @param key
    @return: the parsed information
    """
    gnob = GLBPGP()

    try:
        k = gnob.load_key(key)

        log.debug("Parsed the PGP Key: %s", k['fingerprint'])

        return {
            'public': key,
            'fingerprint': k['fingerprint'],
            'expiration': k['expiration']
        }
    except Exception:
        raise
    finally:
        # the finally statement is always called also if
        # except contains a return or a raise
        gnob.destroy_environment()
