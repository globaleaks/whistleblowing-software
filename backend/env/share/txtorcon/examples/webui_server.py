#!/usr/bin/env python

from __future__ import print_function

from twisted.internet import reactor
from nevow.appserver import NevowSite
from nevow import loaders, tags, livepage
import txtorcon


def setup_failed(fail):
    print("It went sideways!", fail)
    return fail


class TorPage(livepage.LivePage):
    # override for Nevow/twisted.web
    addSlash = True

    # defaults for this class
    continuous_update = True
    ctx = None
    torstate = None

    # Could be done with XHTML 1.0, or a "real" templating language
    docFactory = loaders.stan(
        tags.html[
            tags.head[
                tags.directive('liveglue')],
            tags.body[
                tags.h1["Tor Launching..."],
                # obviously you might want a javascript library or
                # something here instead of this hackery...
                tags.div(id='progress', style='position:abso lute; left:20em; top:10px; width:300px; height:50px; border:2px solid black;background-color:#ffaaaa;')[
                    tags.div(id='progress_done', style='position:absolute; top:0px; left:0px; width:0%; height: 100%; background-color:#aaffaa;')],

                # this is where the messages will go
                tags.div(id='status', style='padding:5px; background-color:#ffaaaa; text-indent:2em; width: 50em; font-weight:bold; border: 2px solid black;')[""]]])

    def goingLive(self, ctx, client):
        '''
        Overrides nevow method; not really safe to just save ctx,
        client in self for multiple clients, but nice and simple.
        '''

        self.ctx = ctx
        self.client = client

    def set_tor_state(self, state):
        self.tor_state = state

    def tor_update(self, percent, tag, summary):
        if self.ctx is None:
            print("I have no Web client yet, but got a Tor update:", percent, tag, summary)
            return

        point = int(300 * (float(percent) / 100.0))
        self.client.send(livepage.js('''document.getElementById('progress_done').style.width = "%dpx";''' % point))

        if percent == 100:
            # done, turn message box green too
            self.client.send(livepage.js('''document.getElementById("status").style.backgroundColor="#aaffaa";'''))

        if self.continuous_update:
            # add a text node for each update, creating a continuous list
            self.client.send(livepage.js('''var newNode = document.createElement('div');
newNode.appendChild(document.createTextNode("%d%% -- %s"));
document.getElementById('status').appendChild(newNode);''' % (percent, summary)))

        else:
            self.client.send(livepage.set('status', "%d%% &mdash; %s" % (percent, summary)))


# This only properly works with one client (the last one to load the
# page). To work with multiples, we'd have to track all clients so
# sending async updates to them worked properly.
top_level = TorPage()

# minimal Tor configuration
config = txtorcon.TorConfig()
config.OrPort = 1234
config.SocksPort = 9999

# launch a Tor based on the above config; the callback will trigger
# when the TorControlProtocol and TorState instances are up and
# running (i.e. Tor process is launched, and we connected to it via
# control protocol and bootstrapped our notion of its state).
d = txtorcon.launch_tor(config, reactor, progress_updates=top_level.tor_update)
d.addCallback(top_level.set_tor_state)
d.addErrback(setup_failed)

print("Launching Tor and providing a Web interface on: \nhttp://localhost:8080\n")

# Start up the Web server
site = NevowSite(top_level)
reactor.listenTCP(8080, site)
reactor.run()
