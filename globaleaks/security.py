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

SALT_LENGTH = 5

def set_password(proposed_password, salt):
    """
    @param proposed_password: a password, not security enforced.
        is not accepted an empty string.

    @return:
        the scrypt hash in base64 of the password
    """
    proposed_password = str(proposed_password)
    salt = str(salt)

    if not len(proposed_password):
        raise errors.InvalidInputFormat("password expected for receiver")

    if len(salt) < SALT_LENGTH:
        raise errors.InvalidInputFormat("used as salt [%s] need to be > than %d" %
                (salt, SALT_LENGTH) )

    hashed_passwd = scrypt.hash(proposed_password, salt[:SALT_LENGTH])
    return binascii.b2a_base64(hashed_passwd)

def check_password(guessed_password, base64_stored, salt):
    assert (len(salt) >= SALT_LENGTH)

    guessed_password = str(guessed_password)
    base64_stored = str(base64_stored)
    salt = str(salt)

    hashed_guessed = scrypt.hash(guessed_password, salt[:SALT_LENGTH])
    return binascii.b2a_base64(hashed_guessed) == base64_stored

def change_password(base64_stored, old_password, new_password, salt):
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
    assert (len(salt) >= SALT_LENGTH)

    base64_stored = str(base64_stored)
    old_password = str(old_password)
    new_password = str(new_password)
    salt = str(salt)

    if not check_password(old_password, base64_stored, salt):
        raise errors.InvalidOldPassword

    return set_password(new_password, salt)


def insert_random_delay():
    """
    Time path analysis tests countermeasure
    """
    centisec = random.randint(1, 100) / 100.0
    time.sleep(centisec)

