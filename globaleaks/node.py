# -*- coding: UTF-8
#   node
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
from globaleaks import Processor
from globaleaks.rest import answers
from globaleaks.utils.dummy import dummy_answers as dummy

class Node(Processor):

    def root_GET(*arg, **kw):

        ret = answers.nodeMainSettings()

        dummy.NODE_ROOT_GET(ret)

        return ret.unroll()
