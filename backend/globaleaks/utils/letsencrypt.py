# -*- coding: utf-
from datetime import datetime
from functools import reduce
from six import text_type
from six.moves import urllib

import OpenSSL
from OpenSSL.crypto import FILETYPE_PEM, load_certificate, dump_certificate

# this import seems unused but it is required in order to load the mocks
from globaleaks.mocks import acme_mocks # pylint: disable=W0611
from globaleaks.utils.utility import log

from acme import messages,challenges, client, messages, crypto_util
import josepy

class ChallTok:
    def __init__(self, tok):
        self.tok = tok


def convert_asn1_date(asn1_bytes):
    return datetime.strptime(text_type(asn1_bytes, 'utf-8'), '%Y%m%d%H%M%SZ')


def create_v2_client(directory_url, accnt_key):
    '''Creates an ACME v2 Client for making requests to Let's Encrypt with'''

    accnt_key = josepy.JWKRSA(key=accnt_key)
    net = client.ClientNetwork(accnt_key, user_agent="GlobalLeaks Let's Encrypt Client")
    directory = messages.Directory.from_json(net.get(directory_url).json())
    acme = client.ClientV2(directory, net)

    return acme

def get_boulder_tos(directory_url, accnt_key):
    '''Returns the TOS for Let's Encrypt from Boulder'''
    client = create_v2_client(directory_url, accnt_key)
    return client.directory.meta.terms_of_service

def run_acme_reg_to_finish(domain, accnt_key, priv_key, hostname, tmp_chall_dict, directory_url):
    '''Runs the entire process of ACME registeration'''

    client = create_v2_client(directory_url, accnt_key)

    # First we need to create a registration with the email address provided
    # and accept the terms of service
    log.info("Using boulder server %s", directory_url)

    client.net.account = client.new_account(
        messages.NewRegistration.from_data(
            terms_of_service_agreed=True
        )
    )

    # Now we need to open an order and request our certificate

    # NOTE: We'll let ACME generate a CSR for our private key as there's
    # a lot of utility code it uses to generate the CSR in a specific
    # fashion. Better to use what LE provides than to roll our own as we
    # we doing with the v1 code
    #
    # This will also let us support multi-domain certificat requests in the
    # future, as well as mandate OCSP-Must-Staple if/when GL's HTTPS server
    # supports it

    csr = crypto_util.make_csr(priv_key, [text_type(hostname, 'utf-8')], False)
    order = client.new_order(csr)
    authzr = order.authorizations

    log.info('Created a new order for %s', hostname)

    # authrz is a list of Authorization resources, we need to find the
    # HTTP-01 challenge and use it
    for auth_req in authzr:
        for chall_body in auth_req.body.challenges:
            if isinstance(chall_body.chall, challenges.HTTP01):
                challb = chall_body
                break

    if challb is None:
        raise Exception("HTTP01 challenge unavailable!")

    response, chall_tok = challb.response_and_validation(client.net.key)

    # This bit of deep magic encode("token") was lifted from certbot to
    # determine the name of the validation file for well-known

    v = chall_body.chall.encode("token")
    log.info('Exposing challenge on %s', v)
    tmp_chall_dict.set(v, ChallTok(chall_tok))

    test_path = 'http://localhost:8082{}'.format(challb.path)
    local_req = urllib.request.Request(test_path, headers={'Host': domain})
    log.debug('Testing local url path: %s', test_path)

    try:
        resp = urllib.request.urlopen(local_req)
        t = resp.read().decode('utf-8').strip()
        if t != chall_tok:
            raise ValueError
    except (IOError, ValueError):
        log.info('Resolving challenge locally failed. ACME request will fail. %s', test_path)
        raise

    cr = client.answer_challenge(challb, challb.response(client.net.key))
    log.debug('Acme CA responded to challenge request with: %s', cr)

    try:
        # Wrap this step and log the failure particularly here because this is
        # the expected point of failure for applications that are not reachable
        # from the public internet.
        order = client.poll_and_finalize(order)

    except messages.Error as error:
        log.err("Failed in request issuance step %s", error)
        raise


    # V2 only returns a full chain certificate, and ACME doesn't ship with
    # helper functions out of the box. Fortunately, searching through cerbot
    # this is easily enough to do with pyOpenSSL

    cert = load_certificate(FILETYPE_PEM, order.fullchain_pem)
    cert_str = dump_certificate(FILETYPE_PEM, cert).decode()
    chain_str = order.fullchain_pem[len(cert_str):].lstrip()

    # pylint: disable=no-member
    expr_date = convert_asn1_date(cert.get_notAfter())
    log.info('Retrieved cert using ACME that expires on %s', expr_date)

    return cert_str, chain_str
