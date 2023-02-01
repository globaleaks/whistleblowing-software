# -*- coding: utf-8 -*-
import base64
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def generate_onion_service_v3():
    b = 256

    def H(m):
        return hashlib.sha512(m).digest()

    def encodeint(y):
        bits = [(y >> i) & 1 for i in range(b)]
        return b''.join([bytes([sum([bits[i * 8 + j] << j for j in range(8)])]) for i in range(b//8)])

    def bit(h, i):
        return (h[i//8] >> (i % 8)) & 1

    def expandSK(sk):
        h = H(sk)
        a = 2**(b-2) + sum(2**i * bit(h, i) for i in range(3, b-2))
        k = b''.join([bytes([h[i]]) for i in range(b//8, b//4)])
        return encodeint(a)+k

    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())

    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)

    # checksum = H(".onion checksum" || pubkey || version)
    checksum = hashlib.sha3_256(b''.join([b'.onion checksum', public_bytes, bytes([0x03])])).digest()[:2]

    # onion_address = base32(pubkey || checksum || version)
    onionAddressBytes = b''.join([public_bytes, checksum, bytes([0x03])])
    onionAddress = base64.b32encode(onionAddressBytes).lower().decode('utf-8')

    return onionAddress + '.onion', 'ED25519-V3:' + base64.b64encode(expandSK(private_bytes)).decode('utf-8')
