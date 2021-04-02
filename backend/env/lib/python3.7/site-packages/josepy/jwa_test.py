"""Tests for josepy.jwa."""
import unittest
from unittest import mock

from josepy import errors, test_util

RSA256_KEY = test_util.load_rsa_private_key('rsa256_key.pem')
RSA512_KEY = test_util.load_rsa_private_key('rsa512_key.pem')
RSA1024_KEY = test_util.load_rsa_private_key('rsa1024_key.pem')
EC_P256_KEY = test_util.load_ec_private_key('ec_p256_key.pem')
EC_P384_KEY = test_util.load_ec_private_key('ec_p384_key.pem')
EC_P521_KEY = test_util.load_ec_private_key('ec_p521_key.pem')


class JWASignatureTest(unittest.TestCase):
    """Tests for josepy.jwa.JWASignature."""

    def setUp(self):
        from josepy.jwa import JWASignature

        class MockSig(JWASignature):
            # pylint: disable=missing-docstring,too-few-public-methods
            # pylint: disable=abstract-class-not-used
            def sign(self, key, msg):
                raise NotImplementedError()  # pragma: no cover

            def verify(self, key, msg, sig):
                raise NotImplementedError()  # pragma: no cover

        # pylint: disable=invalid-name
        self.Sig1 = MockSig('Sig1')
        self.Sig2 = MockSig('Sig2')

    def test_eq(self):
        self.assertEqual(self.Sig1, self.Sig1)

    def test_ne(self):
        self.assertNotEqual(self.Sig1, self.Sig2)

    def test_ne_other_type(self):
        self.assertNotEqual(self.Sig1, 5)

    def test_repr(self):
        self.assertEqual('Sig1', repr(self.Sig1))
        self.assertEqual('Sig2', repr(self.Sig2))

    def test_to_partial_json(self):
        self.assertEqual(self.Sig1.to_partial_json(), 'Sig1')
        self.assertEqual(self.Sig2.to_partial_json(), 'Sig2')

    def test_from_json(self):
        from josepy.jwa import JWASignature
        from josepy.jwa import RS256
        self.assertIs(JWASignature.from_json('RS256'), RS256)


class JWAHSTest(unittest.TestCase):  # pylint: disable=too-few-public-methods

    def test_it(self):
        from josepy.jwa import HS256
        sig = (
            b"\xceR\xea\xcd\x94\xab\xcf\xfb\xe0\xacA.:\x1a'\x08i\xe2\xc4"
            b"\r\x85+\x0e\x85\xaeUZ\xd4\xb3\x97zO"
        )
        self.assertEqual(HS256.sign(b'some key', b'foo'), sig)
        self.assertIs(HS256.verify(b'some key', b'foo', sig), True)
        self.assertIs(HS256.verify(b'some key', b'foo', sig + b'!'), False)


class JWARSTest(unittest.TestCase):

    def test_sign_no_private_part(self):
        from josepy.jwa import RS256
        self.assertRaises(errors.Error, RS256.sign, RSA512_KEY.public_key(), b'foo')

    def test_sign_key_too_small(self):
        from josepy.jwa import RS256
        from josepy.jwa import PS256
        self.assertRaises(errors.Error, RS256.sign, RSA256_KEY, b'foo')
        self.assertRaises(errors.Error, PS256.sign, RSA256_KEY, b'foo')

    def test_rs(self):
        from josepy.jwa import RS256
        sig = (
            b'|\xc6\xb2\xa4\xab(\x87\x99\xfa*:\xea\xf8\xa0N&}\x9f\x0f\xc0O'
            b'\xc6t\xa3\xe6\xfa\xbb"\x15Y\x80Y\xe0\x81\xb8\x88)\xba\x0c\x9c'
            b'\xa4\x99\x1e\x19&\xd8\xc7\x99S\x97\xfc\x85\x0cOV\xe6\x07\x99'
            b'\xd2\xb9.>}\xfd'
        )
        self.assertEqual(RS256.sign(RSA512_KEY, b'foo'), sig)
        self.assertIs(RS256.verify(RSA512_KEY.public_key(), b'foo', sig), True)
        self.assertIs(RS256.verify(
            RSA512_KEY.public_key(), b'foo', sig + b'!'), False)

    def test_ps(self):
        from josepy.jwa import PS256
        sig = PS256.sign(RSA1024_KEY, b'foo')
        self.assertIs(PS256.verify(RSA1024_KEY.public_key(), b'foo', sig), True)
        self.assertIs(PS256.verify(
            RSA1024_KEY.public_key(), b'foo', sig + b'!'), False)

    def test_sign_new_api(self):
        from josepy.jwa import RS256
        key = mock.MagicMock()
        RS256.sign(key, "message")
        self.assertIs(key.sign.called, True)

    def test_sign_old_api(self):
        from josepy.jwa import RS256
        key = mock.MagicMock(spec=[u'signer'])
        signer = mock.MagicMock()
        key.signer.return_value = signer
        RS256.sign(key, "message")
        self.assertIs(key.signer.called, True)
        self.assertIs(signer.update.called, True)
        self.assertIs(signer.finalize.called, True)

    def test_verify_new_api(self):
        from josepy.jwa import RS256
        key = mock.MagicMock()
        RS256.verify(key, "message", "signature")
        self.assertIs(key.verify.called, True)

    def test_verify_old_api(self):
        from josepy.jwa import RS256
        key = mock.MagicMock(spec=[u'verifier'])
        verifier = mock.MagicMock()
        key.verifier.return_value = verifier
        RS256.verify(key, "message", "signature")
        self.assertIs(key.verifier.called, True)
        self.assertIs(verifier.update.called, True)
        self.assertIs(verifier.verify.called, True)


class JWAECTest(unittest.TestCase):

    def test_sign_no_private_part(self):
        from josepy.jwa import ES256
        self.assertRaises(
            errors.Error, ES256.sign, EC_P256_KEY.public_key(), b'foo')

    def test_es256_sign_and_verify(self):
        from josepy.jwa import ES256
        message = b'foo'
        signature = ES256.sign(EC_P256_KEY, message)
        self.assertIs(ES256.verify(EC_P256_KEY.public_key(), message, signature), True)

    def test_es384_sign_and_verify(self):
        from josepy.jwa import ES384
        message = b'foo'
        signature = ES384.sign(EC_P384_KEY, message)
        self.assertIs(ES384.verify(EC_P384_KEY.public_key(), message, signature), True)

    def test_verify_with_wrong_jwa(self):
        from josepy.jwa import ES256, ES384
        message = b'foo'
        signature = ES256.sign(EC_P256_KEY, message)
        self.assertIs(ES384.verify(EC_P384_KEY.public_key(), message, signature), False)

    def test_verify_with_different_key(self):
        from josepy.jwa import ES256
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.backends import default_backend

        message = b'foo'
        signature = ES256.sign(EC_P256_KEY, message)
        different_key = ec.generate_private_key(ec.SECP256R1, default_backend())
        self.assertIs(ES256.verify(different_key.public_key(), message, signature), False)

    def test_sign_new_api(self):
        from josepy.jwa import ES256
        key = mock.MagicMock()
        with mock.patch("josepy.jwa.decode_dss_signature") as decode_patch:
            decode_patch.return_value = (0, 0)
            ES256.sign(key, "message")
        self.assertIs(key.sign.called, True)

    def test_sign_old_api(self):
        from josepy.jwa import ES256
        key = mock.MagicMock(spec=[u'signer'], key_size=256)
        signer = mock.MagicMock()
        key.signer.return_value = signer
        with mock.patch("josepy.jwa.decode_dss_signature") as decode_patch:
            decode_patch.return_value = (0, 0)
            ES256.sign(key, "message")
        self.assertIs(key.signer.called, True)
        self.assertIs(signer.update.called, True)
        self.assertIs(signer.finalize.called, True)

    def test_verify_new_api(self):
        from josepy.jwa import ES256
        key = mock.MagicMock(key_size=256)
        ES256.verify(key, "message", b'\x00' * int(key.key_size / 8) * 2)
        self.assertIs(key.verify.called, True)

    def test_verify_old_api(self):
        from josepy.jwa import ES256
        key = mock.MagicMock(spec=[u'verifier'])
        verifier = mock.MagicMock()
        key.verifier.return_value = verifier
        key.key_size = 65 * 8
        ES256.verify(key, "message", b'\x00' * int(key.key_size / 8) * 2)
        self.assertIs(key.verifier.called, True)
        self.assertIs(verifier.update.called, True)
        self.assertIs(verifier.verify.called, True)

    def test_signature_size(self):
        from josepy.jwa import ES512
        from josepy.jwk import JWK
        key = JWK.from_json(
            {
                'd': 'Af9KP6DqLRbtit6NS_LRIaCP_-NdC5l5R2ugbILdfpv6dS9R4wUPNxiGw-vVWumA56Yo1oBnEm8ZdR4W-u1lPHw5',
                'x': 'PiLhJPInTuJkmQeSkoQ64gKmfogeSfPACWt_7XDVrl2o6xF7fQQQJI3i8XFp4Ca10FIIoHAKruHWrhs-AysxS8U',
                'y': 'cCVfGtpuNzH_IHEY5ueb8OQRAwkrUTr04djfHdXEXlVegpz3cIbgYuho--mFlC9me3kR8TFCg-S3A4whWEEdoVE',
                'crv': 'P-521',
                'kty': 'EC'
            })
        with mock.patch("josepy.jwa.decode_dss_signature") as decode_patch:
            decode_patch.return_value = (0, 0)
            sig = ES512.sign(key.key, b"test")
            self.assertEqual(len(sig), 2 * 66)


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
