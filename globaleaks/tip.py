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

    def main(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def comment(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def files(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def finalize(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def download(self, *arg, **kw):
        return {'arg': arg, 'kw': kw}

    def pertinence(self, *arg, **kw):
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

