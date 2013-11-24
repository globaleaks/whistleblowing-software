# -*- coding: UTF-8
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
from Crypto.Hash import SHA512
from Crypto.Random import random, atfork
from gnupg import GPG

from globaleaks.rest import errors
from globaleaks.utils.utility import log, acquire_bool
from globaleaks.settings import GLSetting
from globaleaks.models import Receiver

SALT_LENGTH = (128 / 8) # 128 bits of unique salt

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
                trusted_absolute_prefix, untrusted_path)

        raise error.DirectoryTraversalException

def get_salt(salt_input):
    """
    @param salt_input:
        A string

    is performed a SHA512 hash of the salt_input string, and are returned 128bits
    of uniq data, converted in
    """
    sha = SHA512.new()
    sha.update(salt_input)
    # hex require two byte each to describe 1 byte of entropy
    return sha.hexdigest()[:SALT_LENGTH * 2]


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
    @param salt:
        You're fine with these

    @param new_password:
        Not security enforced, if wanted, need to be client or handler checked

    @return:
        the scrypt hash in base64 of the new password
    """
    if not check_password(old_password, base64_stored, salt_input):
        log.err("old_password provided do match")
        raise errors.InvalidOldPassword

    check_password_format(new_password)

    return hash_password(new_password, salt_input)


class GLBGPG:
    """
    GPG has not a dedicated class, because one of the function is callend inside a transact, and
    I'm not quite confident on creating an object that operates on the filesystem knowing
    that would be run also on the Storm cycle.
    """

    def __init__(self, receiver_desc):
        """
        every time is needed, a new keyring is created here.
        """
        atfork()

        if receiver_desc.has_key('gpg_key_status') and \
           receiver_desc['gpg_key_status'] != Receiver._gpg_types[1]: # Enabled
            log.err("Requested GPG initialization for a receiver without GPG configured! %s" %
                    receiver_desc['username'])
            raise Exception("Requested GPG init for user without GPG [%s]" % receiver_desc['username'])

        try:
            temp_gpgroot = os.path.join(GLSetting.gpgroot, "%s" % random.randint(0, 0xFFFF) )
            os.makedirs(temp_gpgroot, mode=0700)
            self.gpgh = GPG(gnupghome=temp_gpgroot, options="--trust-model always")
        except Exception as excep:
            log.err("Unable to instance GPG object: %s" % excep)
            raise excep

        self.receiver_desc = receiver_desc
        log.debug("GPG object initialized for receiver %s" % receiver_desc['username'])

    def sanitize_gpg_string(self, received_gpgasc):
        """
        @param received_gpgasc: A gpg armored key
        @return: Sanitized string or raise InvalidInputFormat

        This function validate the integrity of a GPG key
        """
        lines = received_gpgasc.split("\n")
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

            # the C language as left some archetypes in my code
            # [ITA] https://www.youtube.com/watch?v=7jI4DnRJP3k
            i += 1

            try:
                if len(lines[i]) < 2:
                    continue
            except IndexError:
                continue

            main_content = re.compile( r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$" , re.UNICODE)
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

    def validate_key(self, armored_key):
        """
        @param armored_key:
        @return: True or False, True only if a key is effectively importable and listed.
        """

        # or raise InvalidInputFormat
        sanitized_gpgasc = self.sanitize_gpg_string(armored_key)

        try:
            self.ke = self.gpgh.import_keys(sanitized_gpgasc)
        except Exception as excep:
            log.err("Error in GPG import_keys: %s" % excep)
            return False

        # Error reported in stderr may just be warning, this is because is not raise an exception here
        # if self.ke.stderr:
        #     log.err("Receiver %s in uploaded GPG key has raise and alarm:\n< %s >" %
        #             (self.receiver_desc['username'], (self.ke.stderr.replace("\n", "\n  "))[:-3]))

        if not (hasattr(self.ke, 'results') and len(self.ke.results) == 1 and self.ke.results[0].has_key('fingerprint')):
            log.err("User error: unable to import GPG key in the keyring")
            return False

        # else, the key has been loaded and we extract info about that:
        self.fingerprint = self.ke.results[0]['fingerprint']

        # looking if the key is effectively reachable
        try:
            all_keys = self.gpgh.list_keys()
        except Exception as excep:
            log.err("Error in GPG list_keys: %s" % excep)
            return False

        self.keyinfo = u""
        for key in all_keys:
            if key['fingerprint'] == self.fingerprint:

                self.keyinfo += "Key length %s" % key['length']
                try:
                    for uid in key['uids']:
                        self.keyinfo += "\n\t%s" % uid
                except Exception as excep:
                    log.err("Error in GPG key format/properties: %s" % excep)
                    return False

        if not len(self.keyinfo):
            log.err("Key apparently imported but unable to be extracted info")
            return False

        return True


    def encrypt_file(self, plainpath, filestream, output_path):
        """
        @param gpg_key_armor:
        @param plainpath:
        @return:
        """
        if not self.validate_key(self.receiver_desc['gpg_key_armor']):
            raise errors.GPGKeyInvalid

        encrypt_obj = self.gpgh.encrypt_file(filestream, str(self.receiver_desc['gpg_key_fingerprint']))

        if not encrypt_obj.ok:
            # continue here if is not ok
            log.err("Falure in encrypting file %s %s (%s)" % ( plainpath,
                    self.receiver_desc['username'], self.receiver_desc['gpg_key_fingerprint']) )
            log.err(encrypt_obj.stderr)
            raise errors.GPGKeyInvalid

        log.debug("Encrypting for %s (%s) file %s (%d bytes)" %
                  (self.receiver_desc['username'], self.receiver_desc['gpg_key_fingerprint'],
                  plainpath, len(str(encrypt_obj))) )

        encrypted_path = os.path.join( os.path.abspath(output_path),
                                       "gpg_encrypted-%d-%d" %
                                       (random.randint(0, 0xFFFF), random.randint(0, 0xFFFF)))

        if os.path.isfile(encrypted_path):
            log.err("Unexpected unpredictable unbelievable error! %s" % encrypted_path)
            raise errors.InternalServerError("File conflict in GPG encrypted output")

        try:
            with open(encrypted_path, "w+") as f:
                f.write(str(encrypt_obj))

            return encrypted_path, len(str(encrypt_obj))

        except Exception as excep:
            log.err("Error in writing GPG file output: %s (%s) bytes %d" %
                    (excep.message, encrypted_path, len(str(encrypt_obj)) ))
            raise errors.InternalServerError("Error in writing [%s]" % excep.message )


    def encrypt_message(self, plaintext):
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
        if not self.validate_key(self.receiver_desc['gpg_key_armor']):
            raise errors.GPGKeyInvalid

        # This second argument may be a list of fingerprint, not just one
        encrypt_obj = self.gpgh.encrypt(plaintext, str(self.receiver_desc['gpg_key_fingerprint']) )

        if not encrypt_obj.ok:
            # else, is not .ok
            log.err("Falure in encrypting %d bytes for %s (%s)" % (len(plaintext),
                    self.receiver_desc['username'], self.receiver_desc['gpg_key_fingerprint']) )
            log.err(encrypt_obj.stderr)
            raise errors.GPGKeyInvalid

        log.debug("Encrypting for %s (%s) %d byte of plain data (%d cipher output)" %
                  (self.receiver_desc['username'], self.receiver_desc['gpg_key_fingerprint'],
                   len(plaintext), len(str(encrypt_obj))) )

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

    encrypt_notification = acquire_bool(request.get('gpg_enable_notification', False))
    encrypt_file = acquire_bool(request.get('gpg_enable_files', False))

    # set a default status
    receiver.gpg_key_status = Receiver._gpg_types[0]

    if remove_key:
        log.debug("User %s %s request to remove GPG key (%s)" %
                  (receiver.name, receiver.user.username, receiver.gpg_key_fingerprint))

        # In all the cases below, the key is marked disabled as request
        receiver.gpg_key_status = Receiver._gpg_types[0] # Disabled
        receiver.gpg_key_info = None
        receiver.gpg_key_armor = None
        receiver.gpg_key_fingerprint = None
        receiver.gpg_enable_files = False
        receiver.gpg_enable_notification = False

    if receiver.gpg_key_status == Receiver._gpg_types[1]:
        receiver.gpg_enable_files = encrypt_file
        receiver.gpg_enable_notification = encrypt_notification
        log.debug("Receiver %s sets GPG usage: notification %s, file %s" %
                  (receiver.user.username,
                   "YES" if encrypt_notification else "NO",
                   "YES" if encrypt_file else "NO") )

    if new_gpg_key:

        fake_receiver_dict = { 'username' : receiver.user.username }
        gnob = GLBGPG(fake_receiver_dict)
        if not gnob.validate_key(new_gpg_key):
            raise errors.GPGKeyInvalid

        log.debug("GPG Key imported and enabled in file and notification: %s" % gnob.keyinfo)

        receiver.gpg_key_info = gnob.keyinfo
        receiver.gpg_key_fingerprint = gnob.fingerprint
        receiver.gpg_key_status = Receiver._gpg_types[1] # Enabled
        receiver.gpg_key_armor = new_gpg_key
        # default enabled https://github.com/globaleaks/GlobaLeaks/issues/620
        receiver.gpg_enable_files = True
        receiver.gpg_enable_notification = True

        gnob.destroy_environment()


def get_expirations(keylist):
    """
    This function is not implemented in GPG object class because need to operate
    on the whole keys
    """
    atfork()

    try:
        temp_gpgroot = os.path.join(GLSetting.gpgroot, "-expiration_check-%s" % random.randint(0, 0xFFFF) )
        os.makedirs(temp_gpgroot, mode=0700)
        gpexpire= GPG(gnupghome=temp_gpgroot, options="--trust-model always")
    except Exception as excep:
        log.err("Unable to setup expiration check environment: %s" % excep)
        raise excep

    try:
        for key in keylist:
            gpexpire.import_keys(key)
    except Exception as excep:
        log.err("Error in GPG import_keys: %s" % excep)
        raise excep

    try:
        all_keys = gpexpire.list_keys()
    except Exception as excep:
        log.err("Error in GPG list_keys: %s" % excep)
        raise excep

    expirations = {}
    for ak in all_keys:
        expirations.update({ ak['fingerprint'] : ak['date']})

    return expirations


