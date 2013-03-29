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

from globaleaks.rest import errors
from globaleaks.utils import log
from Crypto.Hash import SHA512

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
    proposed_password = str(proposed_password)
    salt = get_salt(salt_input)

    if not len(proposed_password):
        log.err("password string has been not really provided (0 len)")
        raise errors.InvalidInputFormat("password expected for receiver")

    hashed_passwd = scrypt.hash(proposed_password, salt)
    return binascii.b2a_hex(hashed_passwd)


def check_password(guessed_password, base64_stored, salt_input):
    guessed_password = str(guessed_password)
    base64_stored = str(base64_stored)
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
    base64_stored = str(base64_stored)
    old_password = str(old_password)
    new_password = str(new_password)

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

