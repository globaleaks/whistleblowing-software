# -*- coding: utf-8 -*-

from twisted.internet import defer, reactor
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, readBody
from txsocksx.http import SOCKS5Agent

try:
    from twisted.web.client import URI
except ImportError:
    from twisted.web.client import _URI as URI


def get_tor_agent(socks_host='127.0.0.1', socks_port=9050):
    torServerEndpoint = TCP4ClientEndpoint(reactor, socks_host, socks_port)
    agent = SOCKS5Agent(reactor, proxyEndpoint=torServerEndpoint)
    return agent

def get_web_agent():
    return Agent(reactor, connectTimeout=4)

def get_page(agent, url):
    request = agent.request('GET', url)

    def cbResponse(response):
        return readBody(response)

    request.addCallback(cbResponse)

    return request
