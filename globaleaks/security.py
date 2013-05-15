# -*- coding: UTF-8
#
#   security 
#   ********
#
# GlobaLeaks security functions

import scrypt
import binascii
import random
import time
import gnupg

from datetime import timedelta
from Crypto.Hash import SHA512

from globaleaks.rest import errors
from globaleaks.utils import log, timelapse_represent
from globaleaks.settings import GLSetting

SALT_LENGTH = (128 / 8) # 128 bits of unique salt

# this value can be incremented, but instead of the backend enforcing, we
# need a GLClient password strength checker
MINIMUM_PASSWORD_LENGTH = 4


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
        raise errors.InvalidInputFormat("password expected for receiver")

    hashed_passwd = scrypt.hash(proposed_password, salt)
    return binascii.b2a_hex(hashed_passwd)


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

    return hash_password(new_password, salt_input)


def insert_random_delay():
    """
    Time path analysis tests countermeasure
    """
    centisec = random.randint(1, 100) / 100.0
    time.sleep(centisec)


def import_gpg_key(username, armored_key):
    """
    @param username: a real username of the user, here just to be a complete debug
    @param armored_key: the armored GPG key, format not yet checked.
    @return: key summary
    """
    gpgh = gnupg.GPG(gnupghome=GLSetting.gpgroot)
    ke = gpgh.import_keys(armored_key)

    # Error reported in stderr may just be warning, this is because is not raise an exception here
    if ke.stderr:
        log.err("Receiver %s in uploaded GPG key has raise and alarm:\n< %s >" %
                (username, (ke.stderr.replace("\n", "\n  "))[:-3]))

    if hasattr(ke, 'results') and len(ke.results) == 1 and ke.results[0].has_key('fingerprint'):
        fingerprint = ke.results[0]['fingerprint']

        # looking if the key is effectively reachable
        all_keys = gpgh.list_keys()

        if len(all_keys) == 0:
            log.err("Fatal error: unable to read from GPG keyring")
            raise errors.InternalServerError("Unable to perform GPG keys operations")

        keyinfo = u""
        for key in all_keys:
            if key['fingerprint'] == fingerprint:

                lifespan = timedelta(seconds=int(key['date']))
                lifespan_string = timelapse_represent(lifespan.seconds)

                keyinfo += "Key length %s, with %s" % (key['length'], lifespan_string)

                for uid in key['uids']:
                    keyinfo += "\n%s" % uid

                keyinfo += "\nFingerprint: %s" % fingerprint

        log.debug("Receiver %s has uploaded a GPG key [%s]" % (username, fingerprint))

        return (keyinfo, fingerprint)

    else:
        log.err("User error: unable to import GPG key in the keyring")
        raise errors.GPGKeyInvalid


def gpg_encrypt(plaindata, receiver_desc):
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
    gpgh = gnupg.GPG(gnupghome=GLSetting.gpgroot, options="--trust-model always")

    # This second argument may be a list of fingerprint, not just one
    binary_output = gpgh.encrypt(plaindata, str(receiver_desc['gpg_key_fingerprint']) )

    return str(binary_output)
