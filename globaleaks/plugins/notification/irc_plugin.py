from globaleaks.utils import log
from globaleaks.plugins.base import GLPlugin
from ircutils import client

class IRCNotification(GLPlugin):

    def __init__(self):
        self.plugin_name = 'irc'
        self.plugin_type = 'notification'
        self.plugin_description = "IRC notification"

        # this is not the right fields description, because would contain also
        # the 'order' of representation, the 'description' and the 'required' boolean flag
        self.admin_fields = {'server' : 'text', 'channel' : 'text', 'node_user' : 'text' }
        self.receiver_fields = {'receiver_user' : 'text'}

        self.irc_handler = None

    def validate_admin_opt(self, admin_fields):
        return True

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        return True

    def digest_check(self, settings, stored_data, new_data):
        pass

    def _message_printer(self, client, event):
        print "<{0}/{1}> {2}".format(event.source, event.target, event.message)

    def _notice_printer(self, client, event):
        print "(NOTICE) {0}".format(event.message)

    def do_notify(self, settings, stored_data):

        af = settings['admin_fields']
        rf = settings['receiver_fields']

        if not self.irc_handler:
            # Create a SimpleClient instance
            self.irc_handler = client.SimpleClient(nick=af['node_user'])

            # Add the event handlers
            self.irc_handler["channel_message"].add_handler(self._message_printer)
            self.irc_handler["notice"].add_handler(self._notice_printer)

            # Finish setting up the client
            self.irc_handler.connect(af['server'], channel=af['channel'])
            self.irc_handler.start()

        self.irc_handler.send_message(rf['receiver_user'], stored_data)
