"""
    handlers
    ********

    This contains all of the handlers for the REST interface.
    Should not contain any logic that is specific to the operations to be done
    by the particular REST interface.
"""
import json
from twisted.web import resource
from globaleaks.utils.JSONhelper import genericDict
from cyclone import escape
from cyclone.web import RequestHandler

class GLBackendHandler(RequestHandler):
    def prepare(self):
        if self.request.method.lower() is 'post' and \
                self.get_argument('method'):
            self.handle_post_hack(self.get_argument('method'))
        """
        handlers = self._get_host_handlers(request)
        for spec in handlers:
            match = spec.regex.match(request.path)
            if match:
                handler = spec.handler_class(self, request, **spec.kwargs)
                if spec.regex.groups:
                    # None-safe wrapper around url_unescape to handle
                    # unmatched optional groups correctly
                    def unquote(s):
                        if s is None:
                            return s
                        return escape.url_unescape(s, encoding=None)
                    # Pass matched groups to the handler.  Since
                    # match.groups() includes both named and
                    # unnamed groups,we want to use either groups
                    # or groupdict but not both.
                    # Note that args are passed as bytes so the handler can
                    # decide what encoding to use.

                    if spec.regex.groupindex:
                        kwargs = dict(
                            (str(k), unquote(v))
                            for (k, v) in match.groupdict().iteritems())
                    else:
                        args = [unquote(s) for s in match.groups()]
                break
        if not handler:
            handler = ErrorHandler(self, request, status_code=404)

        """

    def handle_post_hack(self, method):
        if method in self.SUPPORTED_METHODS:
            self.request.method = method
        else:
            raise HTTPError(405)

    def get(self, action=None, *arg, **kw):
        print self.request
        self.write({"GET": str(self.__class__)})


    def post(self, action=None, *arg, **kw):
        print self.request
        self.write({"POST": str(self.__class__)})

    def put(self, action=None, *arg, **kw):
        """
        Override these to provide support for
        """
        self.write({'error': 'not supported'})

    def delete(self, action=None, *arg, **kw):
        return {'error': 'not supported'}

class nodeHandler(GLBackendHandler):
    """
    Public resource (P1) /node/.

    Returns all the public information about the node.
    """
    def get(self):
        print self.request
        # self.get_argument('foo')

        retjson = genericDict('render_GET_P1')
        retjson.add_string('FunkyNodeName', 'name')
        retjson.add_string('statz', 'statistic')
        retjson.add_string('BOOLofPROPERTIES', 'node_properties')
        retjson.add_string('This is the description', 'description')
        retjson.add_string('http://funkytransparency.pin', 'public_site')
        retjson.add_string('http://nf940289fn24fewifnm.onion', 'hidden_service')
        retjson.add_string('/', 'url_schema')
        return retjson.printJSON()

class submissionHandler(GLBackendHandler):
    pass

class receiverHandler(GLBackendHandler):
    pass

class adminHandler(GLBackendHandler):
    def get(self, action=None, *arg, **kw):
        pass
    """
        retjson = genericDict('render_GET_A1')
        retjson.add_string('NodeNameForTheAdmin', 'name')
        retjson.add_string('StatisticToBeXXX', 'statistics')
        retjson.add_string('SomePrivateStatsasBefore', 'private_stats')
        retjson.add_string('ConfigurableBooleanParameter', 'node_properties')
        retjson.add_string('thisIStheDescription', 'description')
        retjson.add_string('http://www.globaltest.int/whistleblowing/', 'public_site')
        retjson.add_string('nco2nfio4nioniof2n43.onion', 'hidden_service')
        retjson.add_string('/whistleblowing/', 'url_schema')
        return retjson.printJSON()
    """

class tipHandler(GLBackendHandler):
    pass

