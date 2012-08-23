import cyclone.web
import sys
import json
from twisted.internet import reactor
from twisted.python import log

class SubmissionNewHandler(cyclone.web.RequestHandler):
    def get(self):
        import random
        data = {'receipt': ''.join(str(random.randint(0,10)) for x in
            range(10))}
        print data
        self.write(json.dumps(data))
 
class SubmissionHandler(cyclone.web.RequestHandler):
    def get(self):
        data = [{'name': 'title', 
          'label': 'Title',
          'type': 'string', 
          'hint': 'Insert your title here',
          'default': '',
          'help': 'Place here your help text',
          'required': True},

          {'name': 'description', 
          'label': 'Description',
          'type': 'text', 
          'hint': 'Insert your description here',
          'default': '',
          'help': 'Place here your help text',
          'required': True},

          {'name': 'eyewitness', 
          'label': 'Eye witness?',
          'type': 'checkbox', 
          'help': '',
          'hint': 'check if this applies',
          'required': True},

          {'name': 'othercheckbox', 
          'label': 'Is this true?',
          'type': 'checkbox', 
          'help': '',
          'hint': 'check if this applies',
          'required': False},


          {'name': 'option',
           'label': 'What option?',
           'type': 'radio',
           'help': 'Place here your help text',
           'options': [{'label': 'Option 1', 'value': 'option1'},
                      {'label': 'Option 2', 'value': 'option2'}],
           'hint': 'Pick one of these many options',
           'required': False,
          }
        ]
        self.write(json.dumps(data))

class aboutHandler(cyclone.web.RequestHandler):
    def get(self):
        aboutDict = {'title': 'About this node',
                     'subtitle': 'we rock!',
                     'content': """Sustainable tattooed sriracha, in velit
                     farm-to-table fanny pack kale chips messenger bag. Ethnic
                     deserunt accusamus scenester fixie vegan, blog enim. Retro
                     butcher thundercats lo-fi assumenda, master cleanse occupy
                     aliqua cosby sweater quinoa nesciunt truffaut
                     williamsburg. Mlkshk sed tumblr sunt, cray street art
                     pour-over typewriter. Twee mustache qui cardigan. Freegan
                     adipisicing direct trade deserunt. Anim cliche ennui
                     officia commodo terry richardson."""}
        self.write(json.dumps(aboutDict))

def main():
    log.startLogging(sys.stdout)
    application = cyclone.web.Application([
        (r"/submission/", SubmissionHandler),
        (r"/submission/new", SubmissionNewHandler),
        (r"/about/", aboutHandler),
        (r"/static/(.*)", cyclone.web.StaticFileHandler, {'path': '/home/x/code/web/GLClient/www/'}),
    ])

    reactor.listenTCP(8888, application, interface="127.0.0.1")
    reactor.run()


if __name__ == "__main__":
    main()

