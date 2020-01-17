# -*- coding: utf-8
import ctypes
import os
import sys

from twisted.internet import reactor


def set_proc_title(title):
    """
    Set the process title
    :param title: A title to be assigned to the process
    """
    libc = ctypes.cdll.LoadLibrary('libc.so.6')
    buff = ctypes.create_string_buffer(len(title) + 1)
    buff.value = title.encode()
    libc.prctl(15, ctypes.byref(buff), 0, 0, 0)


def set_pdeathsig(sig):
    """
    Set the PDEATH Signal
    :param sig: A signal that the process need to receive when the parent process dies
    """
    PR_SET_PDEATHSIG = 1
    libc = ctypes.cdll.LoadLibrary('libc.so.6')
    libc.prctl.argtypes = (ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                           ctypes.c_ulong, ctypes.c_ulong)
    libc.prctl(PR_SET_PDEATHSIG, sig, 0, 0, 0)
    # If the parent has already died, kill this process.
    if os.getppid() == 1:
        os.kill(os.getpid(), sig)


def disable_swap():
    """
    Disable the usage of SWAP
    """
    libc = ctypes.CDLL("libc.so.6", use_errno=True)

    MCL_CURRENT = 1
    MCL_FUTURE = 2

    if libc.mlockall(MCL_CURRENT | MCL_FUTURE):
        raise Exception("Failure on mlockall: %s" %
                        os.strerror(ctypes.get_errno()))


def SigQUIT(SIG, FRM):
    """
    Handler of process QUIT signal
    :param SIG: the received signal
    :param FRM: the pid of the
    """
    try:
        if reactor.running:
            reactor.stop()
        else:
            sys.exit(0)
    except:
        pass
