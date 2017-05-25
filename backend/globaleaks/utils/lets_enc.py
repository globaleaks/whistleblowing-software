"""Example script showing how to use acme client API."""
import os
import pkg_resources

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import OpenSSL

from acme import client
from acme import messages
from acme import jose
from acme import challenges

from globaleaks.utils.utility import log


DIRECTORY_URL = 'https://acme-staging.api.letsencrypt.org/directory'
#DIRECTORY_URL = 'https://acme-v01.api.letsencrypt.org/directory'
BITS = 2048  # TODO minimum for Boulder


class ChallTok():
    def __init__(self, tok):
        self.tok = tok


def register_account_key(accnt_key):
    accnt_key = jose.JWKRSA(key=accnt_key)
    acme = client.Client(DIRECTORY_URL, accnt_key)

    regr = acme.register()
    return regr.uri, regr.terms_of_service


def run_acme_reg_to_finish(domain, regr_uri, accnt_key, site_key, csr, tmp_chall_dict):
    '''

    :returns: ``cert`` of `OpenSSL.crypto.X509` certificate wrapped in `acme.jose.util.ComparableX509`
    '''
    accnt_key = jose.JWKRSA(key=accnt_key)
    acme = client.Client(DIRECTORY_URL, accnt_key)
    msg = messages.RegistrationResource(uri=regr_uri)
    regr = acme.query_registration(msg)

    log.info('Auto-accepting TOS: %s from: %s' % (regr.terms_of_service, DIRECTORY_URL))
    acme.agree_to_tos(regr)

    authzr = acme.request_challenges(
        identifier=messages.Identifier(typ=messages.IDENTIFIER_FQDN, value=domain))
    log.debug('Created auth client %s' % authzr)

    def get_http_challenge(x, y):
         if type(y.chall) is challenges.HTTP01:
            return y
         else:
            return x

    challb = reduce(get_http_challenge, authzr.body.challenges, None)
    chall_tok = challb.chall.validation(accnt_key)

    # TODO make sure chall token expires
    v = chall_tok.split('.')[0]
    log.debug('Exposing challenge on %s' % v)
    tmp_chall_dict.set(v, ChallTok(chall_tok))
    log.debug('tmp_chall_dict %s' % tmp_chall_dict)

    try:
       from urllib2 import urlopen
       domain = 'localhost:8082'
       test_path = 'http://{0}{1}'.format(domain, challb.path)
       log.debug('Testing local url path: %s' % test_path)
       #resp = urlopen(test_path)
       #t = resp.read().decode('utf-8').strip()
       #assert t == chall_tok
    except (IOError, AssertionError) as e:
       raise e

    challr = challenges.HTTP01Response()

    cr = acme.answer_challenge(challb, challb.chall.response(accnt_key))
    log.debug('Acme CA responded to challenge with: %s' % cr)

    try:
        (cert, _) = acme.poll_and_request_issuance(jose.util.ComparableX509(csr), (authzr,))
    except messages.Error as error:
        log.err("Failed in last step {0}".format(error))
        raise error

    #TODO(nskelsey) assert returned certificate forms a chain to LEx3 CA
    return cert.body
