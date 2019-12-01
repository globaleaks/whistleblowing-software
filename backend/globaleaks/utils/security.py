# -*- coding: utf-8 -*-
import base64
import binascii
import os
import random
import string
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from globaleaks.rest import errors
from globaleaks.utils.log import log


crypto_backend = default_backend()


def sha256(data):
    h = hashes.Hash(hashes.SHA256(), backend=crypto_backend)

    # Transparently convert str types to bytes
    if isinstance(data, str):
        data = data.encode()

    h.update(data)

    return binascii.b2a_hex(h.finalize())


def sha512(data):
    h = hashes.Hash(hashes.SHA512(), backend=crypto_backend)

    # Transparently convert str types to bytes
    if isinstance(data, str):
        data = data.encode()

    h.update(data)

    return binascii.b2a_hex(h.finalize())


def generateRandomReceipt():
    """
    Return a random receipt of 16 digits
    """
    return ''.join(random.SystemRandom().choice(string.digits) for _ in range(16))


def generateRandomKey(N):
    """
    Return a random key of N characters in a-zA-Z0-9
    """
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(N))


def generateRandomSalt():
    """
    Return a base64 encoded string with 128 bit of entropy
    """

    # Py3 fix explaination: Normally, we'd use str here,
    # however, on Py2, scrypt *wants* str on both Python2/3, (and throws an
    # an exception). As B64 encoded data is always ASCII, this should be
    # able to go safely in and out of the database.

    return base64.b64encode(os.urandom(16)).decode()


def generate_api_token():
    """
    creates an api token along with its corresponding hash digest.

    :rtype: A `tuple` containing (digest `str`, token `str`)
    """
    token = generateRandomKey(32)
    return token, sha512(token.encode())


def directory_traversal_check(trusted_absolute_prefix, untrusted_path):
    """
    check that an 'untrusted_path' matches a 'trusted_absolute_path' prefix
    """
    if not os.path.isabs(trusted_absolute_prefix):
        raise Exception("programming error: trusted_absolute_prefix is not an absolute path: %s" %
                        trusted_absolute_prefix)

    # Windows fix, the trusted_absolute_prefix needs to be normalized for
    # commonprefix to actually work as / is a valid path seperator, but
    # you can end up with things like this: C:\\GlobaLeaks\\client\\app/
    # without it

    untrusted_path = os.path.abspath(untrusted_path)
    trusted_absolute_prefix = os.path.abspath(trusted_absolute_prefix)

    if trusted_absolute_prefix != os.path.commonprefix([trusted_absolute_prefix, untrusted_path]):
        log.err("Blocked file operation for: (prefix, attempted_path) : ('%s', '%s')",
                trusted_absolute_prefix, untrusted_path)

        raise errors.DirectoryTraversalError
