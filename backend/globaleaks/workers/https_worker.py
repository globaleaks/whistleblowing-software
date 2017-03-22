# -*- encoding: utf-8 -*-
import os
import sys

if os.path.dirname(__file__) != '/usr/lib/python2.7/dist-packages/globaleaks/workers':
    sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from twisted.internet import reactor

from globaleaks.workers.process import Process
from globaleaks.utils.sock import listen_tls_on_sock
from globaleaks.utils.sni import SNIMap
from globaleaks.utils.tls import TLSServerContextFactory, ChainValidator
from globaleaks.utils.httpsproxy import HTTPStreamFactory


class HTTPSProcess(Process):
    name = 'gl-https-proxy'
    ports = []

    def __init__(self, *args, **kwargs):
        super(HTTPSProcess, self).__init__(*args, **kwargs)

        proxy_url = 'http://' + self.cfg['proxy_ip'] + ':' + str(self.cfg['proxy_port'])

        http_proxy_factory = HTTPStreamFactory(proxy_url)

        cv = ChainValidator()
        ok, err = cv.validate(self.cfg, must_be_disabled=False)
        if not ok or not err is None:
            raise err

        snimap = SNIMap({
            'DEFAULT': TLSServerContextFactory(self.cfg['ssl_key'],
                                               self.cfg['ssl_cert'],
                                               self.cfg['ssl_intermediate'],
                                               self.cfg['ssl_dh'])
        })

        socket_fds = self.cfg['tls_socket_fds']

        for socket_fd in socket_fds:
            self.log("Opening socket: %d : %s" % (socket_fd, os.fstat(socket_fd)))

            port = listen_tls_on_sock(reactor,
                                      fd=socket_fd,
                                      contextFactory=snimap,
                                      factory=http_proxy_factory)

            self.ports.append(port)
            self.log("HTTPS proxy listening on %s" % port)

    def shutdown(self):
        for port in self.ports:
            port.loseConnection()


if __name__ == '__main__':
    HTTPSProcess().start()
