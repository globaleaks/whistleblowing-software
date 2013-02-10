"""
Marker shifting map:

    The marker present in the models are:

    ReceiverTip    [ u'not notified', u'notified', u'unable to notify', u'notification ignore' ]
    File           [ u'not processed', u'ready', u'blocked', u'stored' ]
    InternalTip    [ u'new', u'first', u'second' ]
    Submission     [ u'incomplete', u'finalized' ]

    ReceiverTip:    shift made by tip_notification()
    File:           shift made by fileprocess()
    InternalTip:    shift made by tip_creation()
    Submission:     shift made by CrudOperation.(new|update)_submission
"""

from globaleaks.transactors.base import MacroOperation
from globaleaks.models.receiver import Receiver
from globaleaks.models.externaltip import File, ReceiverTip, Comment
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.node import Node
from globaleaks.plugins.manager import PluginManager
from globaleaks.settings import config
from globaleaks.rest.errors import ReceiverGusNotFound
from globaleaks.utils.random import get_file_checksum
import os, zipfile

from storm.twisted.transact import transact

class AsyncOperations(MacroOperation):

    @transact
    def tip_notification(self):

        plugin_type = u'notification'
        store = self.getStore()

        receivertip_iface = ReceiverTip(store)

        not_notified_tips = receivertip_iface.get_tips_by_notification_mark(u'not notified')

        node_desc = Node(store).get_single()
        if node_desc['notification_settings'] is None:
            print "This node has not notification configured: postponed notification of ",\
                len(not_notified_tips), "tips"
            return

        for single_tip in not_notified_tips:

        # from a single tip, we need to extract the receiver, and then, having
        # context + receiver, find out which configuration setting has active

            receivers_map = receivertip_iface.get_receivers_by_tip(single_tip['tip_gus'])

            receiver_info = receivers_map['actor']

            # Obtain Notification from Node and from Receveir.notification_fields

            settings_dict = { 'admin_settings' : node_desc['notification_settings'],
                             'receiver_settings' : receiver_info['notification_fields']}

            # hardcoded mail plugin just
            plugin = PluginManager.instance_plugin(u'Mail')

            updated_tip = receivertip_iface.update_notification_date(single_tip['tip_gus'])
            return_code = plugin.do_notify(settings_dict, u'tip', updated_tip)

            if return_code:
               receivertip_iface.flip_mark(single_tip['tip_gus'], u'notified')
            else:
               receivertip_iface.flip_mark(single_tip['tip_gus'], u'unable to notify')

    @transact
    def comment_notification(self):

        plugin_type = u'notification'
        store = self.getStore()

        comment_iface = Comment(store)
        internaltip_iface = InternalTip(store)

        not_notified_comments = comment_iface.get_comment_by_mark(marker=u'not notified')

        node_desc = Node(store).get_single()
        if node_desc['notification_settings'] is None:
            print "This node has not notification configured: postponed notification of",\
                len(not_notified_comments),"comments"
            return

        for comment in not_notified_comments:

            receivers_list = internaltip_iface.get_receivers_by_itip(comment['internaltip_id'])

            # needed to obtain context!
            itip_info = internaltip_iface.get_single(comment['internaltip_id'])

            for receiver_info in receivers_list:

                node_desc = Node(store).get_single()
                settings_dict = { 'admin_settings' : node_desc['notification_settings'],
                                  'receiver_settings' : receiver_info['notification_fields']}

                plugin = PluginManager.instance_plugin(u'Mail')

                return_code = plugin.do_notify(settings_dict, u'comment', comment)

                if return_code:
                    print "Notification of comment successful for user", receiver_info['receiver_gus']
                else:
                    print "Notification of comment failed for user", receiver_info['receiver_gus']

            # remind: comment are not guarantee until Task manager is not developed
            comment_iface.flip_mark(comment['comment_id'], u'notified')


    def do_fileprocess_validation(self, store, context_gus, filepath ):

        plugin_type = u'fileprocess'

        #profile_iface = PluginProfiles(store)
        #profile_associated = profile_iface.get_profiles_by_contexts([ context_gus ] )
        profile_associated = []

        plugin_found = False
        validate_file = False

        for p_cfg in profile_associated:

            # Plugin FileProcess
            if p_cfg['plugin_type'] != plugin_type:
                continue

            plugin_found = True
            print "processing", filepath, "using the profile", p_cfg['profile_gus'], "configured for", p_cfg['plugin_name']

            plugin = PluginManager.instance_plugin(p_cfg['plugin_name'])
            validate_file = plugin.do_fileprocess(filepath, p_cfg['admin_settings'])

        if not plugin_found:
            # FileProcess profile has been not configured, file accepted by default
            validate_file = True

        return validate_file


    @transact
    def fileprocess(self):

        store = self.getStore()

        file_iface = File(store)

        not_processed_file = file_iface.get_file_by_marker(file_iface._marker[0])

        associated_itip = {}
        new_files = {}

        for single_file in not_processed_file:

            itid = single_file['internaltip_id']

            # if InternalTip.id is 0, mean that Submission is not finalized!
            # the file remain marked as 'not processed'.
            if not itid:
                continue

            # collect for logs/info/flow
            associated_itip.update({ itid : InternalTip(store).get_single(itid) })
            # this file log do not contain hash nor path: it's fine anyway
            new_files.update({ single_file['file_gus'] : single_file })

            try:
                tempfpath = os.path.join(config.advanced.submissions_dir, single_file['file_gus'])
                # XXX Access check + stats + length integrity
            except AttributeError:
                # XXX high level danger Log
                continue

            validate_file = self.do_fileprocess_validation(store,single_file['context_gus'], tempfpath)

            # compute hash, SHA256 in non blocking mode (from utils/random.py)
            filehash = get_file_checksum(tempfpath)

            print "Processed:", single_file['file_name'], filehash, "validator response:", validate_file

            if validate_file:
                file_iface.flip_mark(single_file['file_gus'], file_iface._marker[1], filehash) # ready
            else:
                file_iface.flip_mark(single_file['file_gus'], file_iface._marker[2], filehash) # blocked

        return (associated_itip, new_files)


    @transact
    def delivery(self):
        """
        Goal of delivery is checks if some delivery is configured for a context/receiver combo,
        and if is, just delivery the file in the requested way.
        If not, store in the DB and permit downloading.
        """

        plugin_type = u'delivery'
        store = self.getStore()

        file_iface = File(store)
        receivertip_iface = ReceiverTip(store)

        ready_files = file_iface.get_file_by_marker(file_iface._marker[1]) # ready

        for single_file in ready_files:

            # from every file, we need to find the ReceiverTip with the same InternalTip.id
            # This permit to found effectively the receiver that need the file available

            print "Delivery management for", single_file['file_name']

            # Manage special delivery if configured

            tempfpath = os.path.join(config.advanced.submissions_dir, single_file['file_gus'])
            file_iface.add_content_from_fs(single_file['file_gus'], tempfpath)
            file_iface.flip_mark(single_file['file_gus'], file_iface._marker[3]) # stored
            # TODO os.unlink(tempfpath)


    # not yet used
    def _create_zip(self, sourcepath):

        zf = zipfile.ZipFile('/tmp/temp.zip', mode='w')
        try:
            zf.write(sourcepath)
        finally:
            zf.close()

    @transact
    def statistics(self):
        pass

    @transact
    def cleaning(self):
        pass

    @transact
    def check_update(self):
        pass

    @transact
    def tip_creation(self):

        store = self.getStore()

        internaltip_iface = InternalTip(store)
        receiver_iface = Receiver(store)

        internal_tip_list = internaltip_iface.get_itips_by_maker(u'new', False)

        if len(internal_tip_list):
            print "TipSched: found %d new Tip" % len(internal_tip_list)

        for internaltip_desc in internal_tip_list:

            for receiver_gus in internaltip_desc['receivers']:

                try:
                    receiver_desc = receiver_iface.get_single(receiver_gus)
                except ReceiverGusNotFound:
                    # Log error, a receiver has been removed before get the Tip
                    continue

                # check if the Receiver Tier is the first
                if int(receiver_desc['receiver_level']) != 1:
                    continue

                receivertip_obj = ReceiverTip(store)
                receivertip_desc = receivertip_obj.new(internaltip_desc, receiver_desc)
                print "Created rTip", receivertip_desc['tip_gus'], "for", receiver_desc['name'], \
                    "in", internaltip_desc['context_gus']

            internaltip_iface.flip_mark(internaltip_desc['internaltip_id'], internaltip_iface._marker[1])

        # Escalation is not working at the moment, may be well engineered the function
        # before, permitting various layer of receivers.
        #
        # loops over the InternalTip and checks the escalation threshold
        # It may require the creation of second-step Tips
        escalated_itip_list = internaltip_iface.get_itips_by_maker(internaltip_iface._marker[1], True)

        if len(escalated_itip_list):
            print "TipSched: %d Tip are escalated" % len(escalated_itip_list)

        for eitip in escalated_itip_list:
            eitip_id = int(eitip['internaltip_id'])

            # This event has to be notified as system Comment
            Comment(store).new(eitip_id, u"Escalation threshold has been reached", u'system')

            for receiver_gus in eitip['receivers']:

                try:
                    receiver_desc = receiver_iface.get_single(receiver_gus)
                except ReceiverGusNotFound:
                    # Log error, a receiver has been removed before get the Tip
                    continue

                # check if the Receiver Tier is the second
                if int(receiver_desc['receiver_level']) != 2:
                    continue

                receivertip_obj = ReceiverTip(store)
                receivertip_desc = receivertip_obj.new(eitip, receiver_desc)
                print "Created 2nd tir rTip", receivertip_desc['tip_gus'], "for", receiver_desc['name'], \
                    "in", eitip['context_gus']

            internaltip_iface.flip_mark(eitip_id, internaltip_iface._marker[2])

