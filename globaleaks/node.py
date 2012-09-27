# -*- coding: UTF-8
#   node
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks import Processor
from globaleaks.utils import recurringtypes as GLT

class nodeMainSettings(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)

        self.define("public_statistics", GLT.publicStatisticsDict() )
        self.define("public_site", "string")
        self.define("hidden_service", "string")
        self.define("url_schema", "string")
        self.define("name", "string")
        self.define("node_properties", GLT.nodePropertiesDict() )
        """
        variables that may or may not exists:
        'contexts' (Array of contextDescriptionDict() )
        """

class Node(Processor):

    def root_GET(*arg, **kw):

        ret = GLT.publicStatisticsDict()
        return ret.unroll()

