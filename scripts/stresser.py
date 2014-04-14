#!/usr/bin/env python

import json, os

from twisted.internet import protocol, defer, reactor
from twisted.web.iweb import IBodyProducer

from zope.interface import implements

from twisted.web.client import Agent
from twisted.web.http_headers import Headers

base_url = 'http://127.0.0.1:8082'

class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class BodyReceiver(protocol.Protocol):
    def __init__(self, finished, content_length=None):
        self.finished = finished
        self.data = ""
        self.bytes_remaining = content_length

    def dataReceived(self, b):
        self.data += b
        if self.bytes_remaining:
            if self.bytes_remaining == 0:
                self.connectionLost(None)
            else:
                self.bytes_remaining -= len(b)

    def connectionLost(self, reason):
        self.finished.callback(self.data)

def failed(exc, method, url, data, response=None, response_body=None):
    print "[!] %s - %s" % (method, url)
    print "payload: %s" % data
    print "response_body: %s" % response_body
    print "response: %s" % response

@defer.inlineCallbacks
def request(method, url, data=None, session_id=None):
    agent = Agent(reactor)
    headers = {
        'Cookie': ['XSRF-TOKEN=antani;'],
        'X-XSRF-TOKEN': ['antani']
    }
    if session_id:
        headers['X-Session'] = [str(session_id)]

    bodyProducer = None
    if data:
        bodyProducer = StringProducer(json.dumps(data))
    
    try:
        response = yield agent.request(method, str(base_url + url), 
                                       Headers(headers), bodyProducer)
    except Exception as exc:
        failed(exc, method, url, data)
        raise exc

    try:
        content_length = response.headers.getRawHeaders('content-length')
    except IndexError:
        content_length = None

    finished = defer.Deferred()
    response.deliverBody(BodyReceiver(finished, content_length))

    response_body = yield finished
    try:
        d = json.loads(response_body)
    except Exception as exc:
        failed(exc, method, url, data, response, response_body)

    defer.returnValue(d)

class Submission(object):
    def __init__(self, context):
        self.data = {
            'context_id': context['id'],
            'files': '',
            'finalize': False,
            'receivers': context['receivers'],
            'wb_fields': {}
        }
        self.fields = context['fields']
        self.id = None

    @defer.inlineCallbacks
    def create(self):
        response = yield request('POST', '/submission', self.data)

        receivers = self.data['receivers']
        self.data = response
        self.data['receivers'] = [ receivers[0] ]
        # self.data['receivers'] = receivers # some contexts had limits
    
    def randomFill(self):
        self.data['wb_fields'] = {}
        answer_order = 0
        for field in self.fields:
            self.data['wb_fields'][field['key']] = {
		'value' : 'I am an evil stress tester...',
                'answer_order' : answer_order }
            answer_order += 1


    @defer.inlineCallbacks
    def finalize(self):
        self.data['finalize'] = True
        response = yield request('PUT', '/submission/' + self.data['id'], self.data)
        defer.returnValue(response)
        

@defer.inlineCallbacks
def authenticate(password, role, username=''):
    response = yield request('POST', '/authentication', {
        'password': password,
        'role': role,
        'username': username
    })
    defer.returnValue(response)


class WBTip(object):
    def __init__(self, receipt):
        self.receipt = receipt
        self.session_id = None
        self.user_id = None
        
    @defer.inlineCallbacks
    def authenticate(self):
        session = yield authenticate(self.receipt, 'wb')
        self.session_id = session['session_id']
        self.user_id = session['user_id']
    
    def comment(self, text):
        tid = self.user_id
        d = request('POST', '/wbtip/comments',
                     { 'content': "%s%s" % (text, self.receipt) , 
                       'tip_id': tid }, 
                     session_id=self.session_id 
                   )
        @d.addErrback
        def eb(err):
            print err

@defer.inlineCallbacks
def doStuff():
    contexts = yield request('GET', '/contexts')
    for context in contexts:
        print "doStuff ing", context['name']
        sub = Submission(context)
    yield sub.create()
    sub.randomFill()
    submission = yield sub.finalize()
    
    print "Receipt: %s" % submission['receipt']

    tip = WBTip(submission['receipt'])
    yield tip.authenticate()
    yield tip.comment("Your Receipt is:")

    print "Fin."


@defer.inlineCallbacks
def submissionWorkflow(context, request_delay, idx):
    idx -= 1
    sub = Submission(context)
    yield sub.create()
    sub.randomFill()
    submission = yield sub.finalize()

    if idx == 0:
        print "completed %s" % context.name
    else:
        reactor.callLater(request_delay, submissionWorkflow, context, request_delay, idx)

@defer.inlineCallbacks
def submissionFuzz(request_delay, submission_count):
    import time
    print "Using %s - %s" % (request_delay, submission_count)
    contexts = yield request('GET', '/contexts')
  
    i = 0
    while i < submission_count: 
        for cnt, context in enumerate(contexts):
            i += 1
            print "%d) submissionFuzz ing: %s" % (cnt, context['name'])
            time.sleep(0.5)
            # submissionWorkflow(context, request_delay, submission_count)
            doStuff()


submissionFuzz(0, 44)
reactor.run()
