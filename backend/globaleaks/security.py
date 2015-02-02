# -*- coding: utf-8 -*-
#
#   security 
#   ********
#
# GlobaLeaks security functions

import binascii
import re
import os
import shutil
import scrypt
import pickle

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from datetime import datetime

from gnupg import GPG
from tempfile import _TemporaryFileWrapper

from globaleaks.rest import errors
from globaleaks.utils.utility import log, acquire_bool, datetime_null, datetime_to_day_str
from globaleaks.settings import GLSetting
from globaleaks.models import ReceiverTip, Receiver
from globaleaks.third_party.rstr import xeger


SALT_LENGTH = (128 / 8) # 128 bits of unique salt

crypto_backend = default_backend()

class GLSecureTemporaryFile(_TemporaryFileWrapper):
    """
    WARNING!
    You can't use this File object like a normal file object,
    check .read and .write!
    """

    last_action = 'init'

    def __init__(self, filedir):
        """
        filedir: dir target to keep GL.
        """

        self.create_key()

        # XXX remind enhance file name with incremental number
        self.filepath = os.path.join(filedir, "%s.aes" % self.key_id)

        log.debug("++ Creating %s filetmp" % self.filepath)

        self.file = open(self.filepath, 'w+b')

        # last argument is 'True' because the file has to be deleted on .close()
        _TemporaryFileWrapper.__init__(self, self.file, self.filepath, True)

    def initialize_cipher(self):
        self.cipher = Cipher(algorithms.AES(self.key), modes.CTR(self.key_counter_nonce), backend=crypto_backend)
        self.encryptor = self.cipher.encryptor()
        self.decryptor = self.cipher.decryptor()

    def create_key(self):
        """
        Create the AES Key to encrypt uploaded file.
        """
        self.key = os.urandom(GLSetting.AES_key_size)

        self.key_id = xeger(GLSetting.AES_key_id_regexp)
        self.keypath = os.path.join(GLSetting.ramdisk_path, "%s%s" %
                                    (GLSetting.AES_keyfile_prefix, self.key_id))

        while os.path.isfile(self.keypath):
            self.key_id = xeger(GLSetting.AES_key_id_regexp)
            self.keypath = os.path.join(GLSetting.ramdisk_path, "%s%s" %
                                    (GLSetting.AES_keyfile_prefix, self.key_id))

        self.key_counter_nonce = os.urandom(GLSetting.AES_counter_nonce)
        self.initialize_cipher()

        saved_struct = {
            'key' : self.key,
            'key_counter_nonce' : self.key_counter_nonce
        }

        log.debug("Key initialization at %s" % self.keypath)

        with open(self.keypath, 'w') as kf:
            pickle.dump(saved_struct, kf)

        if not os.path.isfile(self.keypath):
            log.err("Unable to write keyfile %s" % self.keypath)
            raise Exception("Unable to write keyfile %s" % self.keypath)

    def avoid_delete(self):
        log.debug("Avoid delete on: %s " % self.filepath)
        self.delete = False

    def write(self, data):
        """
        The last action is kept track because the internal status
        need to track them. read below read()
        """

        assert (self.last_action != 'read'), "you can write after read!"
        
        self.last_action = 'write'
        try:
            if isinstance(data, unicode):
                data = data.encode('utf-8')

            self.file.write(self.encryptor.update(data))
        except Exception as wer:
            log.err("Unable to write() in GLSecureTemporaryFile: %s" % wer.message)
            raise wer

    def close(self):
        if any(x in self.file.mode for x in 'wa') and not self.close_called:
            self.file.write(self.encryptor.finalize())
        return _TemporaryFileWrapper.close(self)

    def read(self, c=None):
        """
        The first time 'read' is called after a write, is automatically seek(0)
        """
        if self.last_action == 'write':
            self.seek(0, 0) # this is a trick just to misc write and read
            self.initialize_cipher()
            log.debug("First seek on %s" % self.filepath)
            self.last_action = 'read'

        if c is None:
            return self.decryptor.update(self.file.read())
        else:
            return self.decryptor.update(self.file.read(c))


class GLSecureFile(GLSecureTemporaryFile):

    def __init__(self, filepath):

        self.filepath = filepath

        self.key_id = os.path.basename(self.filepath).split('.')[0]

        log.debug("Opening secure file %s with %s" % (self.filepath, self.key_id) )

        self.file = open(self.filepath, 'r+b')

        # last argument is 'False' because the file has not to be deleted on .close()
        _TemporaryFileWrapper.__init__(self, self.file, self.filepath, False)

        self.load_key()

    def load_key(self):
        """
        Load the AES Key to decrypt uploaded file.
        """
        self.keypath = os.path.join(GLSetting.ramdisk_path, ("%s%s" % (GLSetting.AES_keyfile_prefix, self.key_id)))

        try:
            with open(self.keypath, 'r') as kf:
                saved_struct = pickle.load(kf)

            self.key = saved_struct['key']
            self.key_counter_nonce = saved_struct['key_counter_nonce']
            self.initialize_cipher()

        except Exception as axa:
            # I'm sorry, those file is a dead file!
            log.err("The file %s has been encrypted with a lost/invalid key (%s)" % (self.keypath, axa.message))
            raise axa


def directory_traversal_check(trusted_absolute_prefix, untrusted_path):
    """
    check that an 'untrusted_path' match a 'trusted_absolute_path' prefix
    """

    if not os.path.isabs(trusted_absolute_prefix):
        raise Exception("programming error: trusted_absolute_prefix is not an absolute path: %s" %
                        trusted_absolute_prefix)

    untrusted_path = os.path.abspath(untrusted_path)

    if trusted_absolute_prefix != os.path.commonprefix([trusted_absolute_prefix, untrusted_path]):
        log.err("Blocked file operation out of the expected path: (\"%s\], \"%s\"" %
                (trusted_absolute_prefix, untrusted_path))

        raise errors.DirectoryTraversalError


def get_salt(salt_input):
    """
    @param salt_input:
        A string

    is performed a SHA512 hash of the salt_input string, and are returned 128bits
    of uniq data, converted in
    """
    sha = hashes.Hash(hashes.SHA512(), backend=crypto_backend)
    sha.update(salt_input.encode('utf-8'))
    # hex require two byte each to describe 1 byte of entropy
    h = sha.finalize()
    digest = binascii.b2a_hex(h)
    return digest[:SALT_LENGTH * 2]


def hash_password(proposed_password, salt_input):
    """
    @param proposed_password: a password, not security enforced.
        is not accepted an empty string.

    @return:
        the scrypt hash in base64 of the password
    """
    proposed_password = proposed_password.encode('utf-8')
    salt = get_salt(salt_input)

    if not len(proposed_password):
        log.err("password string has been not really provided (0 len)")
        raise errors.InvalidInputFormat("Missing password")

    hashed_passwd = scrypt.hash(proposed_password, salt)
    return binascii.b2a_hex(hashed_passwd)


def check_password_format(password):
    """
    @param password:
        a password to be validated

    # A password strength checker need to be implemented in the client;
    # here is implemented a simple validation.
    """
    m1 = re.match(r'.{8,}', password)
    m2 = re.match(r'.*\d.*', password)
    m3 = re.match(r'.*[A-Za-z].*', password)
    if m1 is None or m2 is None or m3 is None:
        raise errors.InvalidInputFormat("password requirements unmet")


def check_password(guessed_password, base64_stored, salt_input):
    guessed_password = guessed_password.encode('utf-8')
    salt = get_salt(salt_input)

    hashed_guessed = scrypt.hash(guessed_password, salt)

    return binascii.b2a_hex(hashed_guessed) == base64_stored


def change_password(base64_stored, old_password, new_password, salt_input):
    """
    @param old_password: The old password in string, expected to be the same.
        If you're workin in Administrative context, just use set_receiver_password
        and override the old one.

    @param base64_stored:
    @param salt_input:
        You're fine with these

    @param new_password:
        Not security enforced, if wanted, need to be client or handler checked

    @return:
        the scrypt hash in base64 of the new password
    """
    if not check_password(old_password, base64_stored, salt_input):
        log.err("change_password_error: provided invalid old_password")
        raise errors.InvalidOldPassword

    check_password_format(new_password)

    return hash_password(new_password, salt_input)


class GLBGPG(object):
    """
    GPG has not a dedicated class, because one of the function is called inside a transact, and
    I'm not quite confident on creating an object that operates on the filesystem knowing
    that would be run also on the Storm cycle.
    """

    def __init__(self):
        """
        every time is needed, a new keyring is created here.
        """
        try:
            temp_gpgroot = os.path.join(GLSetting.gpgroot, "%s" % xeger(r'[A-Za-z0-9]{8}'))
            os.makedirs(temp_gpgroot, mode=0700)
            self.gpgh = GPG(gnupghome=temp_gpgroot, options=['--trust-model', 'always'])
            self.gpgh.encoding = "UTF-8"
        except Exception as excep:
            log.err("Unable to instance GPG object: %s" % excep)
            raise excep

    def sanitize_gpg_string(self, key):
        """
        @param key: A pgp armored key
        @return: Sanitized string or raise InvalidInputFormat

        This function validate the integrity of a GPG key
        """
        lines = key.split("\n")
        sanitized = ""

        start = 0
        if not len(lines[start]):
            start += 1

        if lines[start] != '-----BEGIN PGP PUBLIC KEY BLOCK-----':
            raise errors.InvalidInputFormat("GPG invalid format")
        else:
            sanitized += lines[start] + "\n"

        i = 0
        while i < len(lines):

            # the C language has left some archetypes in my code
            # [ITA] https://www.youtube.com/watch?v=7jI4DnRJP3k
            i += 1

            try:
                if len(lines[i]) < 2:
                    continue
            except IndexError:
                continue

            main_content = re.compile(r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$", re.UNICODE)
            base64only = main_content.findall(lines[i])

            if len(base64only) == 1:
                sanitized += str(base64only[0]) + "\n"

            # this GPG/PGP format it's different from the common base64 ? dunno
            if len(lines[i]) == 5 and lines[i][0] == '=':
                sanitized += str(lines[i]) + "\n"

            if lines[i] == '-----END PGP PUBLIC KEY BLOCK-----':
                sanitized += lines[i] + "\n"
                return sanitized

        raise errors.InvalidInputFormat("Malformed PGP key block")

    def load_key(self, key):
        """
        @param key:
        @return: True or False, True only if a key is effectively importable and listed.
        """
        try:
            sanitized_key = self.sanitize_gpg_string(key)
            import_result = self.gpgh.import_keys(sanitized_key)
        except Exception as excep:
            log.err("Error in GPG import_keys: %s" % excep)
            raise errors.GPGKeyInvalid

        if len(import_result.fingerprints) != 1:
            raise errors.GPGKeyInvalid

        fingerprint = import_result.fingerprints[0]

        # looking if the key is effectively reachable
        try:
            all_keys = self.gpgh.list_keys()
        except Exception as excep:
            log.err("Error in GPG list_keys: %s" % excep)
            raise errors.GPGKeyInvalid

        info = u""
        expiration = datetime.utcfromtimestamp(0)
        for key in all_keys:
            if key['fingerprint'] == fingerprint:

                if key['expires']:
                    expiration = datetime.utcfromtimestamp(int(key['expires']))
                    exp_date = datetime_to_day_str(expiration)
                else:
                    exp_date = u'Never'

                info += "Key length: %s\n" % key['length']
                info += "Key expiration: %s\n" % exp_date

                try:
                    for uid in key['uids']:
                        info += "\t%s\n" % uid
                except Exception as excep:
                    log.err("Error in GPG key format/properties: %s" % excep)
                    raise errors.GPGKeyInvalid

                break

        if not len(info):
            log.err("Key apparently imported but unable to be extracted info")
            raise errors.GPGKeyInvalid

        ret = {
            'fingerprint': fingerprint,
            'expiration': expiration,
            'info': info
        }

        return ret

    def encrypt_file(self, key_fingerprint, plainpath, filestream, output_path):
        """
        @param gpg_key_armor:
        @param plainpath:
        @return:
        """
        encrypt_obj = self.gpgh.encrypt_file(filestream, str(key_fingerprint))

        if not encrypt_obj.ok:
            raise errors.GPGKeyInvalid

        log.debug("Encrypting for key %s file %s (%d bytes)" %
                  (key_fingerprint,
                   plainpath, len(str(encrypt_obj))))

        encrypted_path = os.path.join(os.path.abspath(output_path),
                                      "gpg_encrypted-%s" % xeger(r'[A-Za-z0-9]{8}'))
        try:
            with open(encrypted_path, "w+") as f:
                f.write(str(encrypt_obj))

            return encrypted_path, len(str(encrypt_obj))

        except Exception as excep:
            log.err("Error in writing GPG file output: %s (%s) bytes %d" %
                    (excep.message, encrypted_path, len(str(encrypt_obj)) ))
            raise errors.InternalServerError("Error in writing [%s]" % excep.message)

    def encrypt_message(self, key_fingerprint, plaintext):
        """
        @param plaindata:
            An arbitrary long text that would be encrypted

        @param receiver_desc:

            The output of
                globaleaks.handlers.admin.admin_serialize_receiver()
            dictionary. It contain the fingerprint of the Receiver PUBKEY

        @return:
            The unicode of the encrypted output (armored)

        """
        # This second argument may be a list of fingerprint, not just one
        encrypt_obj = self.gpgh.encrypt(plaintext, str(key_fingerprint))

        if not encrypt_obj.ok:
            raise errors.GPGKeyInvalid

        log.debug("Encrypting for key %s %d byte of plain data (%d cipher output)" %
                  (key_fingerprint,
                   len(plaintext), len(str(encrypt_obj))))

        return str(encrypt_obj)

    def destroy_environment(self):
        try:
            shutil.rmtree(self.gpgh.gnupghome)
        except Exception as excep:
            log.err("Unable to clean temporary GPG environment: %s: %s" % (self.gpgh.gnupghome, excep))


def gpg_options_parse(receiver, request):
    """
    This is called in a @transact, when receiver update prefs and
    when admin configure a new key (at the moment, Admin GUI do not
    permit to sets preferences, but still the same function is
    used.

    @param receiver: the Storm object
    @param request: the Dict receiver by the Internets
    @return: None

    This function is called in create_recever and update_receiver
    and is used to manage the GPG options forced by the administrator

    This is needed also because no one of these fields are
    *enforced* by unicode_keys or bool_keys in models.Receiver

    GPG management, here are check'd these actions:
    1) Proposed a new GPG key, is imported to check validity, and
       stored in Storm DB if not error raise
    2) Removal of the present key

    Further improvement: update the keys using keyserver
    """

    new_gpg_key = request.get('gpg_key_armor', None)
    remove_key = request.get('gpg_key_remove', False)

    # the default
    receiver.gpg_key_status = u'disabled'

    if remove_key:
        log.debug("User %s %s request to remove GPG key (%s)" %
                  (receiver.name, receiver.user.username, receiver.gpg_key_fingerprint))

        # In all the cases below, the key is marked disabled as request
        receiver.gpg_key_status = u'disabled'
        receiver.gpg_key_info = None
        receiver.gpg_key_armor = None
        receiver.gpg_key_fingerprint = None
        receiver.gpg_key_expiration = datetime_null()

    if new_gpg_key:

        try:
            gnob = GLBGPG()

            result = gnob.load_key(new_gpg_key)

            log.debug("GPG Key imported: %s" % result['fingerprint'])

            receiver.gpg_key_status = u'enabled'
            receiver.gpg_key_info = result['info']
            receiver.gpg_key_armor = new_gpg_key
            receiver.gpg_key_fingerprint = result['fingerprint']
            receiver.gpg_key_expiration = result['expiration']

        except:
            raise

        finally:
            # the finally statement is always called also if
            # except contains a return or a raise
            gnob.destroy_environment()


def access_tip(store, user_id, tip_id):
    rtip = store.find(ReceiverTip, ReceiverTip.id == unicode(tip_id),
                      ReceiverTip.receiver_id == user_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    return rtip
