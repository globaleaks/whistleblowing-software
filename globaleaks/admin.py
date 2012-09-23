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

class Admin(Processor):

    # A1
    def node_GET(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return dict(node.info)

    def node_POST(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return dict(node.info)

    # A2
    def contexts_GET(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return  {'iwascalledin': __name__, 'code': 'A2 G'}

    def contexts_POST(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return  {'iwascalledin': __name__, 'code': 'A2 O'}

    def contexts_PUT(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return  {'iwascalledin': __name__, 'code': 'A2 U'}

    def contexts_DELETE(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return  {'iwascalledin': __name__, 'code': 'A2 D'}

    # A3
    def receivers_GET(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return  {'iwascalledin': __name__, 'code': 'A3 G'}

    def receivers_POST(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return  {'iwascalledin': __name__, 'code': 'A3 O'}

    def receivers_PUT(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return  {'iwascalledin': __name__, 'code': 'A3 U'}

    def receivers_DELETE(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return  {'iwascalledin': __name__, 'code': 'A3 D'}

    # A4
    def modules_GET(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return  {'iwascalledin': __name__, 'code': 'A4 G'}

    def modules_POST(self, *arg, **kw):
        print __file__,arg
        print __file__,kw
        return  {'iwascalledin': __name__, 'code': 'A4 O'}



