from globaleaks.utils import log, gltime
from globaleaks.plugins import GLPlugin
# this plugin is based on http://python-irclib.sourceforge.net/
import irc.client

class IRCNotification(GLPlugin):

    def __init__(self):
        self.plugin_name = 'irc'
        self.plugin_description = "IRC notification"

        # this is not the right fields description, because would contain also
        # the 'order' of representation, the 'description' and the 'required' boolean flag
        self.admin_fields = {'server' : 'text', 'channel' : 'text', 'node_user' : 'text' }
        self.receiver_fields = {'receiver_user' : 'text'}

    def validate_admin_opt(self, admin_fields):
        return True

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        return True

    def digest_check(self, settings, stored_data, new_data):
        pass

    def do_notify(self, settings, stored_data):

        af = settings['admin_fields']
        rf = settings['receiver_fields']

        server = irc.client.IRC().server()
        server.connect(af['server'], 6667, af['node_user'])
        server.privmsg(af['channel'], "%s: %s" % (rf['receiver_user'], stored_data) )
        server.socket.close()
