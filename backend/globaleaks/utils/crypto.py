# -*- coding: utf-8 -*-
import base64
import binascii
import os
import random
import secrets
import string
import struct
import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import constant_time, hashes
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.twofactor.totp import TOTP

from nacl.encoding import Base64Encoder
from nacl.hashlib import scrypt
from nacl.pwhash import argon2id
from nacl.public import SealedBox, PrivateKey, PublicKey
from nacl.secret import SecretBox
from nacl.utils import random as nacl_random


crypto_backend = default_backend()


def _convert_to_bytes(arg):
    """
    Convert the argument to bytes if of string type
    :param arg: a string or a byte object
    :return: the converted byte object
    """
    if isinstance(arg, str):
        arg = arg.encode()

    return arg


def _sha(alg, data):
    """
    Perform the sha of the passed data
    :param alg: A specific hash algorithm
    :param data: A data to be hashed
    :return: A hash value
    """
    h = hashes.Hash(alg, backend=crypto_backend)
    h.update(_convert_to_bytes(data))
    return binascii.b2a_hex(h.finalize())


def sha256(data):
    """
    Perform the sha256 of the passed thata
    :param data: A data to be hashed
    :return: A hash value
    """
    return _sha(hashes.SHA256(), data)


def generateOtpSecret():
    """
    Return an OTP secret of 160bit encoded base32
    """
    symbols = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567')
    return ''.join(secrets.choice(symbols) for i in range(32))


def generateRandomKey():
    """
    Return a random secret of 256bits
    """
    return sha256(nacl_random(32)).decode()


def generateRandomPassword(N):
    """
    Return a random password
    """
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(N))


def generate2FA():
    return ''.join(random.SystemRandom().choice(string.digits) for _ in range(8))


def totpVerify(secret, token):
    totp = TOTP(base64.b32decode(secret), 6, SHA1(), 30, crypto_backend, enforce_key_length=False)
    totp.verify(token.encode(), time.time())


def _hash_scrypt(password, salt):
    password = _convert_to_bytes(password)
    salt = _convert_to_bytes(salt)

    # old version of globalealeaks have used hexelify in place of base64;
    # the function is still used for compatibility reasons
    hash = scrypt(password, salt, _GCE.ALGORITM_CONFIGURATION['SCRYPT']['N'])
    return binascii.hexlify(hash).decode()


def _kdf_argon2(password, salt):
    salt = base64.b64decode(salt)
    return argon2id.kdf(32, password, salt[0:16],
                        opslimit=_GCE.ALGORITM_CONFIGURATION['ARGON2']['OPSLIMIT']+1,
                        memlimit=1 << _GCE.ALGORITM_CONFIGURATION['ARGON2']['MEMLIMIT'])


def _hash_argon2(password, salt):
    salt = base64.b64decode(salt)
    hash = argon2id.kdf(32, password, salt[0:16],
                        opslimit=_GCE.ALGORITM_CONFIGURATION['ARGON2']['OPSLIMIT'],
                        memlimit=1 << _GCE.ALGORITM_CONFIGURATION['ARGON2']['MEMLIMIT'])
    return base64.b64encode(hash).decode()


class _StreamingEncryptionObject(object):
    def __init__(self, mode, user_key, filepath):
        self.mode = mode
        self.user_key = user_key
        self.filepath = filepath
        self.key = None
        self.EOF = False

        self.index = 0

        if self.mode == 'ENCRYPT':
            self.fd = open(filepath, 'wb')
            self.key = nacl_random(32)
            self.partial_nonce = nacl_random(16)
            key = _GCE.asymmetric_encrypt(self.user_key, self.key)
            self.fd.write(key)
            self.fd.write(self.partial_nonce)
        else:
            self.fd = open(filepath, 'rb')
            x = self.fd.read(80)
            self.key = _GCE.asymmetric_decrypt(self.user_key, x)
            self.partial_nonce = self.fd.read(16)

        self.box = SecretBox(self.key)

    def fullNonce(self, i):
        return self.partial_nonce + struct.pack('<Q', i)

    def lastFullNonce(self):
        return self.partial_nonce + struct.pack('>Q', 1)

    def getNextNonce(self, last):
        if last:
            chunkNonce = self.lastFullNonce()
        else:
            chunkNonce = self.fullNonce(self.index)

        self.index += 1

        return chunkNonce

    def encrypt_chunk(self, chunk, last=0):
        chunkNonce = self.getNextNonce(last)
        self.fd.write(struct.pack('>B', last))
        self.fd.write(struct.pack('>I', len(chunk)))
        self.fd.write(self.box.encrypt(chunk, chunkNonce)[24:])

    def decrypt_chunk(self):
        last = struct.unpack('>B', self.fd.read(1))[0]
        if last:
            self.EOF = True

        chunkNonce = self.getNextNonce(last)
        chunkLen = struct.unpack('>I', self.fd.read(4))[0]
        chunk = self.fd.read(chunkLen + 16)
        return last, self.box.decrypt(chunk, chunkNonce)

    def read(self, a):
        if not self.EOF:
            return self.decrypt_chunk()[1]

    def close(self):
        if self.fd is not None:
            self.fd.close()
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()


class _GCE(object):
    # Warning: KDF options by design should be greater than HASH optionsENCRYPTION_AVA
    ALGORITM_CONFIGURATION = {
        'ARGON2': {
            'MEMLIMIT': 27,  # 128MB
            'OPSLIMIT': 16
        },
        'SCRYPT': {
            'N': 1 << 14  # Value used in old protocol
        }
    }

    KDF_FUNCTIONS = {}

    HASH_FUNCTIONS = {
        'SCRYPT': _hash_scrypt
    }

    KDF_FUNCTIONS['ARGON2'] = _kdf_argon2
    HASH_FUNCTIONS['ARGON2'] = _hash_argon2

    @staticmethod
    def generate_receipt():
        """
        Return a random receipt of 16 digits
        """
        return ''.join(random.SystemRandom().choice(string.digits) for _ in range(16))

    @staticmethod
    def generate_salt():
        """
        Return a salt with 128 bit of entropy
        """
        return base64.b64encode(os.urandom(16)).decode()

    @staticmethod
    def hash_password(password, salt, algorithm='ARGON2'):
        """
        Return the hash a password using a specified algorithm
        If the algorithm provided is none uses the best available algorithm
        """
        password = _convert_to_bytes(password)
        salt = _convert_to_bytes(salt)

        return _GCE.HASH_FUNCTIONS[algorithm](password, salt)

    @staticmethod
    def check_password(algorithm, password, salt, hash):
        """
        Perform passowrd check for match with a provided hash
        """
        password = _convert_to_bytes(password)
        salt = _convert_to_bytes(salt)
        hash = _convert_to_bytes(hash)
        x = _convert_to_bytes(_GCE.HASH_FUNCTIONS[algorithm](password, salt))

        return constant_time.bytes_eq(x, hash)

    @staticmethod
    def generate_key():
        """
        Generate a 256 bit key
        """
        return nacl_random(32)

    @staticmethod
    def derive_key(password, salt):
        """
        Perform key derivation from a user password
        """
        password = _convert_to_bytes(password)
        salt = _convert_to_bytes(salt)

        return _GCE.KDF_FUNCTIONS['ARGON2'](password, salt)

    @staticmethod
    def generate_keypair():
        """
        Generate a curve25519 keypair
        """
        prv_key = PrivateKey.generate()

        return prv_key.encode(Base64Encoder), \
               prv_key.public_key.encode(Base64Encoder)

    @staticmethod
    def generate_recovery_key(prv_key):
        rec_key = _GCE.generate_key()
        pub_key = PrivateKey(prv_key, Base64Encoder).public_key.encode(Base64Encoder)
        bkp_key = _GCE.symmetric_encrypt(rec_key, prv_key)
        rec_key = _GCE.asymmetric_encrypt(pub_key, rec_key)
        return Base64Encoder.encode(bkp_key), Base64Encoder.encode(rec_key)

    @staticmethod
    def symmetric_encrypt(key, data):
        """
        Perform symmetric encryption using libsodium secretbox (XSalsa20-Poly1305))
        """
        nonce = nacl_random(24)
        data = _convert_to_bytes(data)
        return SecretBox(key).encrypt(data, nonce)

    @staticmethod
    def symmetric_decrypt(key, data):
        """
        Perform symmetric decryption using libsodium secretbox (XSalsa20-Poly1305)
        """
        data = _convert_to_bytes(data)
        return SecretBox(key).decrypt(data)

    @staticmethod
    def asymmetric_encrypt(pub_key, data):
        """
        Perform asymmetric encryption using libsodium sealedbox (Curve25519, XSalsa20-Poly1305)
        """
        pub_key = PublicKey(pub_key, Base64Encoder)
        data = _convert_to_bytes(data)
        return SealedBox(pub_key).encrypt(data)

    @staticmethod
    def asymmetric_decrypt(prv_key, data):
        """
        Perform asymmetric decryption using libsodium sealedbox (Curve25519, XSalsa20-Poly1305)
        """
        prv_key = PrivateKey(prv_key, Base64Encoder)
        data = _convert_to_bytes(data)
        return SealedBox(prv_key).decrypt(data)

    @staticmethod
    def streaming_encryption_open(mode, user_key, filepath):
        return _StreamingEncryptionObject(mode, user_key, filepath)


GCE = _GCE()
