# This launches Tor and starts an Onion service using Twisted and
# txtorcon, and then starts a Web server using the aiohttp library.
#
# This style of interop between asyncio and Twisted requires twisted
# to use the "asyncioreactor" and for code to convert Futures/Tasks to
# Deferreds (most of which is already in Deferred)
#
# Thanks to Mark Williams for the inspiration, and this code:
# https://gist.github.com/markrwilliams/bffb9c293194d105169ea06f03484ba1
#
# note: if run in Python2, there are SyntaxErrors before we can tell
# the user nicely

import os
import asyncio
from twisted.internet import asyncioreactor

# get our reactor installed as early as possible, in case other
# imports decide to import a reactor and we get the default
asyncioreactor.install(asyncio.get_event_loop())

from twisted.internet.task import react
from twisted.internet.defer import ensureDeferred, Deferred
from twisted.internet.endpoints import UNIXClientEndpoint

import txtorcon
try:
    import aiohttp
    from aiohttp import web
    from aiosocks.connector import ProxyConnector, ProxyClientRequest
except ImportError:
    raise Exception(
        "You need aiohttp to run this example:\n  pip install aiohttp"
    )


def as_future(d):
    return d.asFuture(asyncio.get_event_loop())


def as_deferred(f):
    return Deferred.fromFuture(asyncio.ensure_future(f))


def get_slash(request):
    return web.Response(
        text="I am an aiohttp Onion service\n",
    )


def create_aio_application():
    app = web.Application()
    app.add_routes([
        web.get('/', get_slash)
    ])
    return app


async def _main(reactor):
    if False:
        print("launching tor")
        tor = await txtorcon.launch(reactor, progress_updates=print)
    else:
        tor = await txtorcon.connect(reactor,
            UNIXClientEndpoint(reactor, "/var/run/tor/control")
        )
    config = await tor.get_config()
    print("Connected to tor {}".format(tor.version))

    # here, we've just chosen 1234 as the port. We have three other
    # options:
    # - select a random, unused one ourselves
    # - put "ports=[80]" below, and find out which port txtorcon
    #   selected after
    # - use a Unix-domain socket

    # we create a Tor onion service on a specific local TCP port
    print("Creating onion service")
    onion = await tor.create_onion_service(
        ports=[
            (80, 1234)  # 80 is the 'public' port, 1234 is local
        ],
        private_key='RSA1024:MIICWwIBAAKBgQCmHEH1y7/RUUeeaSTgB3iQFfWMep38JDlAbDoEPltRxzgEh8bXMsNbemdiCuZmJVni96KrRh2/I2NwWi6C81xfcA8BjVzdCmEbL1B+KOeqZlrjoEMQl56NpbXIIzFZdyILaQtv3EZMoShNHSkta6e66oWUu2B2fkluwYyPxRAdvQIDAQABAoGAYkObHX2PlpK/jE1k3AZvYsUqwhSTOuJu39ZmJ7Z/rQvt7ngnv4wvFwF9APmzvD9iQir+FtXeqQCVRZSDqUGvpW0WgA+8aDA3BGWCZwKhWRWj18RLjsMX+wKP6OBpSIlNjELU8zc5PWWsCmT7AqAdVD7vqp2895LiP4M8vwwZB30CQQDb/fjoG1VWpFWXgjRHEYOoPj7d7J5FcRrbSgc57lvMv/2+4OVl2aRaGEjigfBnR7Pjbyxv/5K1h078PBWNumjPAkEAwUyN3SLJOMBM74LS2jh9AB/sNitLT7/O1f8zT0siC58TmTbeZsj3VqSsmrUiVSptQcOm+5F0UPvYxsI+B2UbswJAdV9dq8jZkS6AlCNd7QUFL4B2XkVedEJSR+mJTXlE9UsCARNQkTS7oW4PhPo633+8FH4+QUskZUHZ/G26OjHYtQJAIAKyd418LzbBRuSuUE8MfEnND0dqKGHGOfASKi5yC+SjFTtd5z2eoC2TG+elMN9eyoZBD+YNkh+yzW97YDQhOwJAKFKLmdlJve1lJah1ZllZfk2ipNeYVX+q1Mv7TE6IXGqU/Xt3HS8h9Zd8ml/Yms1z9X7hFIjQ/XcSiJhqcin8Vg==',
        version=2,  # FIXME use v3; using old tor for now
        progress=print,
    )

    # we're now listening on some onion service URL and re-directing
    # public port 80 requests to local TCP port 1234.
    app = create_aio_application()
    runner = web.AppRunner(app)
    await as_deferred(runner.setup())
    site = web.TCPSite(runner, 'localhost', 1234)
    await as_deferred(site.start())

    # now we're completely set up
    print("Onion site on http://{}".format(onion.hostname))
    await Deferred()


def main():
    return react(
        lambda reactor: ensureDeferred(
            _main(reactor)
        )
    )

if __name__ == '__main__':
    main()
