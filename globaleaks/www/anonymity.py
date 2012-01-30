import socket

from socksipy import socks
from torctl import TorCtl

class TorHandler(TorCtl):
    """
    A new Socket class based on torctl, and handler for tor.
    """

    # basic command line
    #torproc

    def __new__(cls, *args, **kwargs):
        """
        Before creating a new socket, we must check tor daemon is active, and
        otherwise lauch it.

        Return a new socketobject, None if launching tor daemon failed.
        """
        cls._torctl = TorCrl()

        # if tor is started
        if not cls._torctl.connect():
            try:
                cls.__start()
            except OSError:
                return None

        return super(cls, socket.__socketobject).__new__(*args, **kwargs)



def start_tor():
    """
    Start tor daemon in a new process.
    """
    raise NotImplementedError

def torsocks():
    """
    Change socket.socket to a socksproxy binded to tor proxy.
    """
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "localhost", 9050)
    socket.socket = socks.socksocket
