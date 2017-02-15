from globaleaks.workers.procproto import ProcessProtocol


class HTTPSProcProtocol(ProcessProtocol):
    def __init__(self, supervisor, cfg, cfg_fd=42):
        ProcessProtocol.__init__(self, supervisor, cfg, cfg_fd)

        for tls_socket_fd in cfg['tls_socket_fds']:
            self.fd_map[tls_socket_fd] = tls_socket_fd
