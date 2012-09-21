# -*- coding: UTF-8
#   tip
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Contains all the logic for handling tip related operations.

from globaleaks import Processor

class Tip(Processor):

    def root_GET(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    """
    root of /tip/ POST handle deleting and forwarding options,
    they are checked in the tip-properties 
    (assigned by the tip propetary)
    """
    def root_POST(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def comment_POST(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def files_GET(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def files_PUT(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def files_POST(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def files_DELETE(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def finalize_POST(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def download_GET(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    """
    pertinence is marked as GET, but need to be a POST,
    either because a receiver may express +1 -1 values,
    and because can be extended in the future
    """
    def pertinence_POST(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    """
    TODO - import_filds of
    tipStatistic (representation of one single Tip)
    tipIndexDict (list of minimal info of all Tip)
    """

    """
    TODO - dummyDict of tipStatistic and tipIndexDict
    """

    """
    XXX
        GLBackend/docs/RestJSONwrappers.md address to "tipStatistics" but in fact
        would be renamed in tipWholeDict, because contain all the info
        for the WB/receiver in a Tip.

        maybe useful fork with different stats for the admin ?
    """

