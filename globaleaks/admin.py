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
from globaleaks.utils import recurringtypes as GLT


class nodeMainSettings(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)

        self.define("name", "string")
        self.define("admin_statistics", GLT.adminStatisticsDict() )
        self.define("public_statistics", GLT.publicStatisticsDict() )
        self.define("node_properties", GLT.nodePropertiesDict() )

        # self.define("node_description", GLT.localizationDict() )
        # localizationDict -- i need to understand how can be interfaced
        # with POT files

        """
        variables that may or may not exists:
        'contexts' (Array of contextDescriptionDict() )
        """
        self.define("public_site", "string")
        self.define("hidden_service", "string")
        self.define("url_schema", "string")


class adminContextsCURD(GLT.GLTypes):
    def __init__(self):
        GLT.GLTypes.__init__(self, self.__class__.__name__)

class adminReceiverCURD(GLT.GLTypes):
    def __init__(self):
        GLT.GLTypes.__init__(self, self.__class__.__name__)

class adminModulesUR(GLT.GLTypes):
    def __init__(self):
        GLT.GLTypes.__init__(self, self.__class__.__name__)


class Admin(Processor):

    # A1
    """
    Get the node main settings, update the node main settings
    """
    def node_GET(self, *arg, **kw):

        ret = nodeMainSettings()
        ret.name = "NodeNameGetByDB"

        # if some contexts are available ...
        ret.define("contexts", GLT.contextDescriptionDict() )
        ret.extension("contexts", GLT.contextDescriptionDict() )
        ret.extension("contexts", GLT.contextDescriptionDict() )

        return ret.unroll()

    def node_POST(self, *arg, **kw):
        return self.node_GET(arg, kw)


    # A2
    """
    classic CURD in the 'contexts'
    """
    def contexts_GET(self, *arg, **kw):

        ret = adminContextsCURD()

        # if some contexts are available ...
        ret.define("contexts", GLT.contextDescriptionDict() )
        ret.extension("contexts", GLT.contextDescriptionDict() )
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

        ret = adminReceiverCURD()

        # if some receivers are present...
        ret.define("receivers", GLT.receiverDescriptionDict() )
        ret.extension("receivers", GLT.receiverDescriptionDict() )
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

        ret = adminModulesUR()

        # append here the available modules
        ret.define("modules", GLT.moduleDataDict() )
        ret.extension("modules", GLT.moduleDataDict() )

    def modules_POST(self, *arg, **kw):
        return self.modules_GET(arg, kw)

