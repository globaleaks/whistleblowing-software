# -*- coding: utf-8
import josepy
import re

from datetime import datetime
from acme import challenges, client, crypto_util, messages
from six import text_type

from globaleaks.utils.utility import log


class ChallTok:
    def __init__(self, tok):
        self.tok = tok

def split_certificate_chain(full_chain_pem):
    certificates = re.findall('-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----', full_chain_pem, re.DOTALL)
    return certificates[0], ''.join(certificates[1:])


def convert_asn1_date(asn1_bytes):
    return datetime.strptime(text_type(asn1_bytes, 'utf-8'), '%Y%m%d%H%M%SZ')


def create_v2_client(directory_url, accnt_key):
    """Creates an ACME v2 Client for making requests to Let's Encrypt with"""

    accnt_key = josepy.JWKRSA(key=accnt_key)
    net = client.ClientNetwork(accnt_key, user_agent="GlobaLeaks Let's Encrypt Client")
    directory = messages.Directory.from_json(net.get(directory_url).json())

    return client.ClientV2(directory, net)


def get_boulder_tos(directory_url, accnt_key):
    """Returns the TOS for Let's Encrypt from Boulder"""
    return create_v2_client(directory_url, accnt_key).directory.meta.terms_of_service


def run_acme_reg_to_finish(domain, accnt_key, priv_key, hostname, tmp_chall_dict, directory_url):
    """Runs the entire process of ACME registeration"""

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
    csr = crypto_util.make_csr(priv_key, [hostname], False)
    order = client.new_order(csr)
    authzr = order.authorizations

    log.info('Created a new order for %s', hostname)

    # authrz is a list of Authorization resources, we need to find the
    # HTTP-01 challenge and use it
    for auth_req in authzr: # pylint: disable=not-an-iterable
       for chall_body in auth_req.body.challenges:
            if isinstance(chall_body.chall, challenges.HTTP01):
                challb = chall_body
                break

    if challb is None:
        raise Exception("HTTP01 challenge unavailable!")

    response, chall_tok = challb.response_and_validation(client.net.key)
    v = chall_body.chall.encode("token")
    log.info('Exposing challenge on %s', v)
    tmp_chall_dict.set(v, ChallTok(chall_tok))

    cr = client.answer_challenge(challb, challb.response(client.net.key))
    log.debug('Acme CA responded to challenge request with: %s', cr)

    order = client.poll_and_finalize(order)

    return split_certificate_chain(order.fullchain_pem)
