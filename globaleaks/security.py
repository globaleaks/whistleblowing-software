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

from datetime import timedelta
from Crypto.Hash import SHA512
from gnupg import GPG

from globaleaks.rest import errors
from globaleaks.utils import log, timelapse_represent
from globaleaks.settings import GLSetting
from globaleaks.models import Receiver

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

    try:
        gpgh = GPG(gnupghome=GLSetting.gpgroot, options="--trust-model always")
    except Exception as excep:
        log.err("Unable to instance GPG object: %s" % str(excep))
        raise excep

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

                # lifespan = timedelta(seconds=int(key['date']))
                # lifespan_string = timelapse_represent(lifespan.seconds)
                # keyinfo += "Key length %s, with %s" % (key['length'], lifespan_string)

                keyinfo += "Key length %s" % key['length']

                for uid in key['uids']:
                    keyinfo += "\n\t%s" % uid

        log.debug("Receiver %s has a new GPG key: %s" % (username, fingerprint))
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
    try:
        gpgh = GPG(gnupghome=GLSetting.gpgroot, options="--trust-model always")
    except Exception as excep:
        log.err("Unable to instance GPG object: %s" % str(excep))
        raise excep

    ke = gpgh.import_keys(receiver_desc['gpg_key_armor'])
    # here need to be trapped the 'expired' or 'revoked' attribute

    if hasattr(ke, 'results') and len(ke.results) == 1 and ke.results[0].has_key('fingerprint'):
        fingerprint = ke.results[0]['fingerprint']
        if not fingerprint == receiver_desc['gpg_key_fingerprint']:
            log.err("Something is weird. I don't know if someone has played with the DB. I give up")
            raise errors.GPGKeyInvalid

    # This second argument may be a list of fingerprint, not just one
    encrypt_obj = gpgh.encrypt(plaindata, str(receiver_desc['gpg_key_fingerprint']) )

    if encrypt_obj.ok:
        log.debug("Encrypting for %s (%s) %d byte of plain data (%d cipher output)" %
                  (receiver_desc['username'], receiver_desc['gpg_key_fingerprint'],
                   len(plaindata), len(str(encrypt_obj))) )

        return str(encrypt_obj)

    # else, is not .ok
    log.err("Falure in encrypting %d bytes for %s (%s)" % (len(plaindata),
        receiver_desc['username'], receiver_desc['gpg_key_fingerprint']) )
    log.err(encrypt_obj.stderr)
    raise errors.GPGKeyInvalid



def gpg_clean():
    pass


# This is called in a @transact!
def gpg_options_manage(receiver, request):
    """
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
    encrypt_notification = request.get('gpg_enable_notification', False)
    encrypt_file = request.get('gpg_enable_notification', False)

    receiver.gpg_key_status = Receiver._gpg_types[0]
    receiver.gpg_enable_notificiation = False
    receiver.gpg_enable_files = False

    if remove_key:
        log.debug("User %s request to remove GPG key (%s)" %
                  (receiver.username, receiver.gpg_key_fingerprint))

        # In all the cases below, the key is marked disabled as request
        receiver.gpg_key_status = Receiver._gpg_types[0] # Disabled
        receiver.gpg_key_info = receiver.gpg_key_armor = receiver.gpg_key_fingerprint = None

    if new_gpg_key:

        log.debug("Importing a new GPG key for user %s" % receiver.username)

        key_info, key_fingerprint = import_gpg_key(receiver.username, new_gpg_key)

        if not key_info or not key_fingerprint:
            log.err("GPG Key import failure")
            raise errors.GPGKeyInvalid

        log.debug("GPG Key import success: %s" % receiver.gpg_key_info)

        receiver.gpg_key_info = key_info
        receiver.gpg_key_fingerprint = key_fingerprint
        receiver.gpg_key_status = Receiver._gpg_types[1] # Enabled
        receiver.gpg_key_armor = new_gpg_key

        gpg_clean()
        # End of GPG key management for receiver

    if encrypt_file or encrypt_notification:
        if receiver.gpg_key_status == Receiver._gpg_types[1]:
            receiver.gpg_enable_files = encrypt_file
            receiver.gpg_enable_notification = encrypt_notification
            log.debug("Receiver %s sets GPG usage: notification %s, file %s" %
                (receiver.username,
                 "YES" if encrypt_notification else "NO",
                 "YES" if encrypt_file else "NO")
            )
        else:
            log.err("Gpg unset, but %s has put True in notif/file encryption ?" % receiver.username)
            # Just a silent error logging.

