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

class Admin(Processor):
    def node(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def context(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def groups(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def receivers(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

