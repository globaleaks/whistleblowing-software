import json

from twisted.web import resource, static, server
from twisted.application import internet, service

f = open('markdown1.md')
markdown1 = ''.join(f.readlines())
f.close()
f = open('markdown2.md')
markdown2 = ''.join(f.readlines())
f.close()


latenza_example_site = {'title': 'Lorem ipsum',
            'menu': {'foobar': '/latenza/foobar',
                      'barfoo': '/latenza/barfoo'},
            'submenu': {'foo': '/latenza/foo'},
            'content': [markdown1, {'type': 'fileupload',
                                    'value': 'foobar'},
                        markdown2]
           }

class HTTPLatenza(resource.Resource):
    isLeaf = True
    def render(self, request):
        return json.dumps(latenza_example_site)

class HTTPBackend(resource.Resource):
    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild('static', static.File('/home/x/code/web/latenza.js/www/'))
        self.putChild('latenza', HTTPLatenza())

application = service.Application('latenza')
sc = service.IServiceCollection(application)
i = internet.TCPServer(8080, server.Site(HTTPBackend()))
i.setServiceParent(sc)

