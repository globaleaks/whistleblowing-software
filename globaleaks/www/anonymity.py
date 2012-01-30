import socket

import socks
from torctl import TorCtl

_torpath = 'tor'
_torport = 56323


def once(func):
    """
    Closure for functions that should run only once.
    """
    def decorator(*args, **kwargs):
        if not func.has_run:
            func.has_run = True
            return func(*args, **kwargs)

    func.has_run = False
    return decorator


@once
def start_tor():
    """
    Start tor daemon in a new process.
    """
    raise NotImplementedError

@once
def torsocks():
    """
    Change socket.socket to a socksproxy binded to tor proxy.
    """
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "localhost", _torport)
    socket.socket = socks.socksocket


def tor_running(func):
    """
    Closure for services requiring tor.
    If tor is active, return func, a IOError raising function otherwise
    """
    def no_tor(*args, **kwargs):
        raise IOError('Tor not running')

    conn = TorCtl.connect()
    if not conn:
        return
    else:
        conn.close()
        return func

class TorListener(TorCtl.PostEventListener):
    """
    Listener for tor events.
    """

    def __new__(cls, events=None, *args, **kwargs):
        """
        Before creating a new socket, we must check tor daemon is active, and
        otherwise lauch it.

        Return a new socketobject, None if launching tor daemon failed.
        """
        conn = TorCtl.connect()

        if not conn and not start_tor():
            return None
        else:
            cls._conn = conn
            conn.set_events(events or ["BW"])
            return super(cls, TorCtl.EventListener).__new__(*args, **kwargs)

    def brandwith_event(self, event):
        """
        Log informations about current brandwidth.
        """

    def logtorevent(self, event):
        """
        Log informations about events on tor stream.
        """

    @property
    def running(self):
        return self._conn.is_alive()

