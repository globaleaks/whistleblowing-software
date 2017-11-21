# -*- coding: utf-8 -*-
from txsocksx.http import SOCKS5Agent

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web.client import Agent, readBody


def get_tor_agent(socks_host='127.0.0.1', socks_port=9050):
    """
    An HTTP agent that uses SOCKS5 to proxy all requests through the socks_port

    It is implicitly understood that the socks_port points to the locally
    configured tor daemon
    """
    torServerEndpoint = TCP4ClientEndpoint(reactor, socks_host, socks_port)

    return SOCKS5Agent(reactor, proxyEndpoint=torServerEndpoint)


def get_web_agent():
    """An HTTP agent that connects to the web without using Tor"""
    return Agent(reactor, connectTimeout=5)


def get_page(agent, url):
    request = agent.request('GET', url)

    request.addCallback(readBody)

    return request
