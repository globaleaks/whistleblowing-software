import os
from datetime import datetime

def log():
    pid = os.getpid()
    def prefix(m):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S%z')
        print('%s [gl-https-proxy:%d] %s' % (now, pid, m))
    return prefix


# TODO: make this conditional and abstract it with a worker class
# When this executable is not within the systems standard path, the globaleaks
# module must add it to sys path manually. Hence the following line.
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from datetime import datetime
from urlparse import urlparse

from twisted.internet import reactor

from globaleaks.workers.process import Process
from globaleaks.utils.sock import listen_tls_on_sock
from globaleaks.utils.tls import TLSServerContextFactory, ChainValidator
from globaleaks.utils.httpsproxy import HTTPStreamFactory

class HTTPSProcess(Process):
    name = 'gl-https-proxy'
    ports = []

    def __init__(self, *args, **kwargs):
        super(HTTPSProcess, self).__init__(*args, **kwargs)

        proxy_url = 'http://' + self.cfg['proxy_ip'] + ':' + str(self.cfg['proxy_port'])
        res = urlparse(proxy_url)
        if not res.hostname in ['127.0.0.1', 'localhost']:
            raise Exception('Attempting to proxy to an external host: %s . . aborting' % proxy_url)

        http_proxy_factory = HTTPStreamFactory(proxy_url)

        cv = ChainValidator()
        ok, err = cv.validate(self.cfg, must_be_disabled=False)
        if not ok or not err is None:
            raise err

        tls_factory = TLSServerContextFactory(self.cfg['ssl_key'],
                                              self.cfg['ssl_cert'],
                                              self.cfg['ssl_intermediate'],
                                              self.cfg['ssl_dh'])

        socket_fds = self.cfg['tls_socket_fds']

        for socket_fd in socket_fds:
            self.log("Opening socket: %d : %s" % (socket_fd, os.fstat(socket_fd)))

            port = listen_tls_on_sock(reactor,
                                      fd=socket_fd,
                                      contextFactory=tls_factory,
                                      factory=http_proxy_factory)

            self.ports.append(port)
            self.log("HTTPS proxy listening on %s" % port)

    def shutdown(self):
        for port in self.ports:
            port.loseConnection()


if __name__ == '__main__':
    try:
        https_process = HTTPSProcess()
        https_process.start()
    except Exception as e:
        print("setup failed with %s" % e)
        raise
