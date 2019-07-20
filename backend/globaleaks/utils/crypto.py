# -*- coding: utf-8 -*-
import base64
import binascii
import os
import random
import string
import struct

from distutils.version import LooseVersion as V  # pylint: disable=no-name-in-module,import-error

# python-scrypt is still used because not all the versions of pynacl/cryptography includes it
# this library could be replaced later on in the project
import scrypt

import nacl
if V(nacl.__version__) >= V('1.2'):
    from nacl.encoding import RawEncoder, HexEncoder
    from nacl.pwhash import argon2id  # pylint: disable=no-name-in-module
    from nacl.public import SealedBox, PrivateKey, PublicKey  # pylint: disable=no-name-in-module
    from nacl.secret import SecretBox
    from nacl.utils import random as nacl_random

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import constant_time, hashes

from six import text_type


crypto_backend = default_backend()


def _convert_to_bytes(arg):
    if isinstance(arg, text_type):
        arg = arg.encode('utf-8')

    return arg


def _sha(alg, data):
    h = hashes.Hash(alg, backend=crypto_backend)
    h.update(_convert_to_bytes(data))
    return binascii.b2a_hex(h.finalize())


def sha256(data):
    return _sha(hashes.SHA256(), data)


def sha512(data):
    return _sha(hashes.SHA512(), data)


def generateApiToken():
    token = generateRandomKey(32)
    return token, sha512(token.encode())


def generate2FA():
    return ''.join(random.SystemRandom().choice(string.digits) for _ in range(8))


def generateRandomKey(N):
    """
    Return a random key of N characters in a-zA-Z0-9
    """
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(N))


def _hash_scrypt(password, salt):
    password = _convert_to_bytes(password)
    salt = _convert_to_bytes(salt)

    # old version of globalealeaks have used hexelify in place of base64;
    # the function is still used for compatibility reasons
    return binascii.hexlify(scrypt.hash(password, salt, N=GCE.ALGORITM_CONFIGURATION['HASH']['SCRYPT']['N'])).decode('utf-8')


if V(nacl.__version__) >= V('1.2'):
    def _kdf_argon2(password, salt):
        salt = base64.b64decode(salt)
        return argon2id.kdf(32, password, salt[0:16],
                            opslimit=GCE.ALGORITM_CONFIGURATION['KDF']['ARGON2']['OPSLIMIT'],
                            memlimit=GCE.ALGORITM_CONFIGURATION['KDF']['ARGON2']['MEMLIMIT'])

    def _hash_argon2(password, salt):
        salt = base64.b64decode(salt)
        hash = argon2id.kdf(32, password, salt[0:16],
                            opslimit=GCE.ALGORITM_CONFIGURATION['HASH']['ARGON2']['OPSLIMIT'],
                            memlimit=GCE.ALGORITM_CONFIGURATION['HASH']['ARGON2']['MEMLIMIT'])
        return base64.b64encode(hash).decode('utf-8')

    class _StreamingEncryptionObject(object):
        def __init__(self, mode, user_key, filepath):
            self.mode = mode
            self.user_key = user_key
            self.filepath = filepath
            self.key = None
            self.EOF = False

            self.index = 0

            if self.mode =='ENCRYPT':
                self.fd = open(filepath, 'wb')
                self.key = nacl_random(32)
                self.partial_nonce = nacl_random(16)
                key = GCE.asymmetric_encrypt(self.user_key, self.key)
                self.fd.write(key)
                self.fd.write(self.partial_nonce)
            else:
                self.fd = open(filepath, 'rb')
                x = self.fd.read(80)
                self.key = GCE.asymmetric_decrypt(self.user_key, x)
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


class GCE(object):
    # Warning: KDF options by design should be greater than HASH options
    ENCRYPTION_AVAILABLE = V(nacl.__version__) >= V('1.2')
    ALGORITM_CONFIGURATION = {
        'KDF': {
            'ARGON2': {
                'MEMLIMIT': 1 << 27,  # 128MB
                'OPSLIMIT': 17
            }
        },
        'HASH': {
            'ARGON2': {
                'MEMLIMIT': 1 << 27,  # 128MB
                'OPSLIMIT': 16
            },
            'SCRYPT': {
                'N': 1 << 14  # Value used in old protocol
            }
        }
    }

    KDF_FUNCTIONS = {}

    HASH_FUNCTIONS = {
        'SCRYPT': _hash_scrypt
    }

    HASH = 'ARGON2'
    if V(nacl.__version__) >= V('1.2'):
        KDF_FUNCTIONS['ARGON2'] = _kdf_argon2
        HASH_FUNCTIONS['ARGON2'] = _hash_argon2
    else:
        HASH = 'SCRYPT'

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
    def hash_password(password, salt, algorithm=None):
        """
        Return the hash a password using a specified algorithm
        If the algorithm provided is none uses the best available algorithm
        """
        password = _convert_to_bytes(password)
        salt = _convert_to_bytes(salt)

        if algorithm is None:
            algorithm = GCE.HASH

        return GCE.HASH_FUNCTIONS[algorithm](password, salt)

    @staticmethod
    def check_password(algorithm, password, salt, hash):
        """
        Perform passowrd check for match with a provided hash
        """
        password = _convert_to_bytes(password)
        salt = _convert_to_bytes(salt)
        hash = _convert_to_bytes(hash)
        x = _convert_to_bytes(GCE.HASH_FUNCTIONS[algorithm](password, salt))

        return constant_time.bytes_eq(x, hash)

    if V(nacl.__version__) >= V('1.2'):
        @staticmethod
        def generate_key():
            """
            Generate a 128 bit key
            """
            return nacl_random(32)

        @staticmethod
        def derive_key(password, salt):
            """
            Perform key derivation from a user password
            """
            password = _convert_to_bytes(password)
            salt = _convert_to_bytes(salt)

            return GCE.KDF_FUNCTIONS['ARGON2'](password, salt)

        @staticmethod
        def generate_keypair():
            """
            Generate a curbe25519 keypair
            """
            prv_key = PrivateKey.generate()

            return prv_key.encode(RawEncoder), \
                   prv_key.public_key.encode(RawEncoder)

        @staticmethod
        def import_private_key(private_key):
            return PrivateKey(private_key, HexEncoder)

        @staticmethod
        def export_private_key(private_key):
            return PrivateKey(private_key, RawEncoder).encode(HexEncoder).decode('utf-8')

        @staticmethod
        def generate_private_key_backup(private_key):
            key = GCE.generate_key()
            backup = GCE.symmetric_encrypt(key, private_key)
            return key, backup

        @staticmethod
        def load_private_key_backup(key, backup):
            return GCE.symmetric_decrypt(key, backup)

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
            pub_key = PublicKey(pub_key, RawEncoder)
            data = _convert_to_bytes(data)
            return SealedBox(pub_key).encrypt(data)

        @staticmethod
        def asymmetric_decrypt(prv_key, data):
            """
            Perform asymmetric decryption using libsodium sealedbox (Curve25519, XSalsa20-Poly1305)
            """
            prv_key = PrivateKey(prv_key, RawEncoder)
            data = _convert_to_bytes(data)
            return SealedBox(prv_key).decrypt(data)

        @staticmethod
        def streaming_encryption_open(mode, user_key, filepath):
            return _StreamingEncryptionObject(mode, user_key, filepath)
