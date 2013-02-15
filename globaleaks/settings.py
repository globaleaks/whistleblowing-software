# -*- coding: UTF-8
#   config
#   ******
#
# Configuration file do not contain GlobaLeaks Node information, like in the 0.1
# because all those infos are stored in the databased.
# Config contains some system variables usable for debug, integration with APAF and
# nothing in the common concern af a GlobaLeaks Node Admin


import os
import os.path
import sys
import traceback

import transaction
from twisted.python import log
from twisted.python.threadpool import ThreadPool
from twisted.internet import reactor
from storm.twisted.transact import Transactor
from storm import exceptions
from twisted.internet.threads import deferToThreadPool
from cyclone.util import ObjectDict as OD
from cyclone.web import HTTPError
from storm.zope.zstorm import ZStorm
from storm.tracer import debug


root_path = os.path.join(os.path.dirname(__file__), '..')
install_path = os.path.abspath(os.path.join(root_path, '..'))
glclient_path = os.path.join(install_path, 'GLClient', 'app')
gldata_path = os.path.join(root_path, '_gldata')
db_file = 'sqlite:' + os.path.join(gldata_path, 'glbackend.db')
create_db_file = os.path.join(root_path, 'globaleaks', 'db', 'sqlite.sql')

store_name = 'main_store'
# threads sizes
db_thread_pool_size = 1
# loggings
import logging
## set to false to disable file logging
logfile = '/tmp/glbackend.log'
loglevel = logging.DEBUG

# plugins
notification_plugins = [
        'MailNotification',
]


if not os.path.exists(gldata_path):
        os.mkdir(gldata_path)

assert all(os.path.exists(path) for path in
           (root_path, install_path, glclient_path, gldata_path))



class transact(object):
    """
    Class decorator for managing transactions.
    Because storm sucks.
    """
    tp = ThreadPool(0, db_thread_pool_size)

    def __init__(self, method):
        self.method = method
        self.instance = None

    def __get__(self, instance, owner):
        self.instance = instance
        return self

    def __call__(self,  *args, **kwargs):
        return self.run(self._wrap, self.method, *args, **kwargs)

    @staticmethod
    def run(function, *args, **kwargs):
        return deferToThreadPool(reactor, transact.tp, function, *args, **kwargs)

    @staticmethod
    def get_store():
        zstorm = ZStorm()
        zstorm.set_default_uri(store_name, db_file)
        return zstorm.get(store_name)

    def _wrap(self, function, *args, **kwargs):
        self.store = self.get_store()
        try:
            if self.instance:
                result = function(self.instance, self.store, *args, **kwargs)
            else:
                result = function(self.store, *args, **kwargs)
        except (exceptions.IntegrityError, exceptions.DisconnectionError) as e:
            log.msg(e)
            transaction.abort()
            result = None
        except HTTPError as e:
            transaction.abort()
            raise e
        except Exception:
            transaction.abort()
            type, value, tb = sys.exc_info()
            traceback.print_tb(tb, 10)
            self.store.close()
            # propagate the exception
            raise value
        else:
            self.store.commit()
        finally:
            self.store.close()

        return result


if 'db' in sys.argv:
    debug(True, sys.stdout)
else:
    debug(False, sys.stdout)

# xxx. move this on another place
sessions = dict()

transact.tp.start()
reactor.addSystemEventTrigger('after', 'shutdown', transact.tp.stop)

