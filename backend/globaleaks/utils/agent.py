# -*- coding: utf-8 -*-
from globaleaks.utils.socks import SOCKS5Agent

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web.client import Agent, readBody


def get_tor_agent(socks_port=9999):
    """
    An HTTP agent that uses SOCKS5 to proxy all requests through the socks_port

    It is implicitly understood that the socks_port points to the locally
    configured tor daemon
    :param socks_host: the sock host
    :param socks_port: the sock port
    :return: an initialized agent using the specificed sock config
    """
    torServerEndpoint = TCP4ClientEndpoint(reactor, b"127.0.0.1", socks_port)

    return SOCKS5Agent(reactor, proxyEndpoint=torServerEndpoint)


def get_web_agent():
    """An HTTP agent that connects to the web without using Tor
    :return: A simple initialized agent
    """
    return Agent(reactor, connectTimeout=5)


def get_page(agent, url):
    """Perform a get request to the specified url and return response content
    :param agent: An agent to be used to issue the request
    :param url: A url to be fetched
    :return: A content returned by the url resource
    """
    return agent.request(b'GET', url).addCallback(readBody)
