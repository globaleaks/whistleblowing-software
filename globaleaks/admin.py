# -*- coding: UTF-8
#
#   admin
#   *****
#
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#

from globaleaks import Processor
from globaleaks import node
from globaleaks.rest import answers
from globaleaks.utils.dummy import dummy_answers as dummy


class Admin(Processor):

    # A1
    """
    Get the node main settings, update the node main settings
    """
    def node_GET(self, *arg, **kw):

        ret = answers.nodeMainSettings()

        dummy.ADMIN_NODE_GET(ret)

        return ret.unroll()

    def node_POST(self, *arg, **kw):
        return self.node_GET(arg, kw)


    # A2
    """
    classic CURD in the 'contexts'
    """
    def contexts_GET(self, *arg, **kw):

        ret = answers.adminContextsCURD()

        dummy.ADMIN_CONTEXTS_GET(ret)

        return ret.unroll()

    def contexts_POST(self, *arg, **kw):
        return self.contexts_GET(arg, kw)

    def contexts_PUT(self, *arg, **kw):
        return self.contexts_GET(arg, kw)

    def contexts_DELETE(self, *arg, **kw):
        return self.contexts_GET(arg, kw)


    # A3
    """
    classic CURD in the 'receivers'
    """
    def receivers_GET(self, *arg, **kw):

        ret = answers.adminReceiverCURD()

        dummy.ADMIN_RECEIVERS_GET(ret)

        return ret.unroll()

    def receivers_POST(self, *arg, **kw):
        return self.receivers_GET(arg, kw)

    def receivers_PUT(self, *arg, **kw):
        return self.receivers_GET(arg, kw)

    def receivers_DELETE(self, *arg, **kw):
        return self.receivers_GET(arg, kw)


    # A4
    """
    A limited CURD (we've not creation|delete, just update, with
    maybe a flag that /disable/ a module)
    """
    def modules_GET(self, *arg, **kw):

        ret = answers.adminModulesUR()

        dummy.ADMIN_MODULES_GET(ret)

        return ret

    def modules_POST(self, *arg, **kw):
        return self.modules_GET(arg, kw)

