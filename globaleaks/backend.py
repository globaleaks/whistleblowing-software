import json
from twisted.web import server, resource, http
import globaleaks
from globaleaks.rest import RESTful, EmptyChild

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor
    reactor.listenTCP(8082, server.Site(RESTful()))
    reactor.run()

