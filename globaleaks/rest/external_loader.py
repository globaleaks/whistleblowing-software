from twisted.web import resource

"""
This file is a test, 
emulate an external module, when need to load a dedicated REST interface 
"""

__all__ = [ 'simulation_of_module_loading_rest' ]

def simulation_of_module_loading_rest():

    class internalHandler(resource.Resource):

        def __init__(self, name="module_exteral_test"):
            self.name = name
            resource.Resource.__init__(self)

        def render_GET(self, request):
            print name + "GET" + str(request)
            return name + "GET" + str(request)

        def render_POST(self, request):
            print name + "POST" + str(request)
            return name + "POST" + str(request)
  
    modular_rest = internalHandler()
    print "putChild di external_test", str(internalHandler)
    modular_rest.putChild("/external_test/", internalHandler() )

