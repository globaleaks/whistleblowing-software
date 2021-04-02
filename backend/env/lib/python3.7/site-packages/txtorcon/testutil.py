from twisted.internet import defer

from zope.interface import implementer

from txtorcon.interface import ITorControlProtocol


@implementer(ITorControlProtocol)
class FakeControlProtocol(object):
    """
    This is a little weird, but in most tests the answer at the top of
    the list is sent back immediately in an already-called
    Deferred. However, if the answer list is empty at the time of the
    call, instead the returned Deferred is added to the pending list
    and answer_pending() may be called to have the next Deferred
    fire. (see test_accept_all_postbootstrap for an example).

    It is done this way in case we need to have some other code run
    between the get_conf (or whatever) and the callback -- if the
    Deferred is already-fired when get_conf runs, there's a Very Good
    Chance (always?) that the callback just runs right away.
    """

    def __init__(self, answers):
        self.answers = answers
        self.pending = []
        self.post_bootstrap = defer.succeed(self)
        self.on_disconnect = defer.Deferred()
        self.sets = []
        self.events = {}  #: event type -> callback
        self.pending_events = {}  #: event type -> list
        self.is_owned = -1
        self.version = "0.2.8.0"
        # XXX can we get rud of 'commands' and just use pending?
        self.commands = []

    def queue_command(self, cmd):
        if len(self.answers) == 0:
            d = defer.Deferred()
            self.pending.append(d)
            self.commands.append((cmd, d))
            return d

        d = defer.succeed(self.answers[0])
        self.commands.append((cmd, d))
        self.answers = self.answers[1:]
        return d

    def event_happened(self, event_type, *args):
        '''
        Use this in your tests to send 650 events when an event-listener
        is added.  XXX Also if we've *already* added one? Do that if
        there's a use-case for it
        '''
        if event_type in self.events:
            self.events[event_type](*args)
        elif event_type in self.pending_events:
            self.pending_events[event_type].append(args)
        else:
            self.pending_events[event_type] = [args]

    def answer_pending(self, answer):
        d = self.pending[0]
        self.pending = self.pending[1:]
        d.callback(answer)

    def get_info(self, info):
        a = self.answers.pop()
        return defer.succeed(a)

    def get_info_raw(self, info):
        if len(self.answers) == 0:
            d = defer.Deferred()
            self.pending.append(d)
            return d

        d = defer.succeed(self.answers[0])
        self.answers = self.answers[1:]
        return d

    @defer.inlineCallbacks
    def get_info_incremental(self, info, cb):
        text = yield self.get_info_raw(info)
        for line in text.split('\r\n'):
            cb(line)
        defer.returnValue('')  # FIXME uh....what's up at torstate.py:350?

    def get_conf(self, info):
        if len(self.answers) == 0:
            d = defer.Deferred()
            self.pending.append(d)
            return d

        d = defer.succeed(self.answers[0])
        self.answers = self.answers[1:]
        return d

    get_conf_raw = get_conf  # up to test author ensure the answer is a raw string
    get_conf_single = get_conf

    def set_conf(self, *args):
        for i in range(0, len(args), 2):
            self.sets.append((args[i], args[i + 1]))
        return defer.succeed('')

    def add_event_listener(self, nm, cb):
        self.events[nm] = cb
        if nm in self.pending_events:
            for event in self.pending_events[nm]:
                cb(*event)
        return defer.succeed(None)

    def remove_event_listener(self, nm, cb):
        del self.events[nm]
