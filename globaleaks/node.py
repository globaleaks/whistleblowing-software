# -*- coding: UTF-8
#   node
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks import Processor
from globaleaks.utils import recurringtypes as GLT
from globaleaks.utils import dummy

class nodeMainSettings(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)

        self.define("name", "string")
        self.define("public_site", "string")
        self.define("hidden_service", "string")
        self.define("url_schema", "string")
        self.define("node_properties", GLT.nodePropertiesDict() )
        self.define("public_statistics", GLT.publicStatisticsDict() )
        self.define_array("contexts", GLT.contextDescriptionDict() )

class Node(Processor):

    def root_GET(*arg, **kw):

        ret = nodeMainSettings()

        dummy.NODE_ROOT_GET(ret)

        return ret.unroll()
