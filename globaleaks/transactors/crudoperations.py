from globaleaks.transactors.base import MacroOperation

from globaleaks.models.context import Context
from globaleaks.models.receiver import Receiver
from globaleaks.models.externaltip import File, ReceiverTip, WhistleblowerTip, Comment
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.submission import Submission
from globaleaks.models.options import PluginProfiles, ReceiverConfs

from storm.twisted.transact import transact

class CrudOperations(MacroOperation):
    """
    README.md describe pattern and reasons
    """

    @transact
    def get_context_list(self):

        context_iface = Context(self.getStore())
        all_contexts = context_iface.get_all()

        self.returnData(all_contexts)
        self.returnCode(200)
        self.returnValues()

    @transact
    def create_context(self, request):

        store = self.getStore()

        context_iface = Context(store)

        context_description_dict = context_iface.new(request)
        new_context_gus = context_description_dict['context_gus']

        # 'receivers' it's a relationship between two tables, and is managed
        # with a separate method of new()
        receiver_iface = Receiver(store)

        context_iface.context_align(new_context_gus, request['receivers'])
        receiver_iface.full_receiver_align(new_context_gus, request['receivers'])

        context_description = context_iface.get_single(new_context_gus)

        self.returnData(context_description)
        self.returnCode(201)
        return self.returnValues()


    @transact
    def get_context(self, context_gus):

        context_iface = Context(self.getStore())
        context_description = context_iface.get_single(context_gus)

        self.returnData(context_description)
        self.returnCode(200)
        return self.returnValues()

    @transact
    def update_context(self, context_gus, request):

        store = self.getStore()

        context_iface = Context(store)
        context_iface.update(context_gus, request)

        # 'receivers' it's a relationship between two tables, and is managed
        # with a separate method of update()
        receiver_iface = Receiver(store)
        context_iface.context_align(context_gus, request['receivers'])
        receiver_iface.full_receiver_align(context_gus, request['receivers'])

        context_description = context_iface.get_single(context_gus)

        self.returnData(context_description)
        self.returnCode(200)
        return self.returnValues()

    @transact
    def delete_context(self, context_gus):
        """
        This DELETE operation, its permanent, and remove all the reference
        a Context has within the system (Tip, File, submission...)
        """
        store = self.getStore()

        # Get context description, just to verify that context_gus is valid
        context_iface = Context(store)
        context_desc = context_iface.get_single(context_gus)

        # Collect tip by context and iter on the list
        receivertip_iface = ReceiverTip(store)
        tips_related_blocks = receivertip_iface.get_tips_by_context(context_gus)

        internaltip_iface = InternalTip(store)
        whistlebtip_iface = WhistleblowerTip(store)
        file_iface = File(store)
        comment_iface = Comment(store)

        # For every InternalTip, delete comment, wTip, rTip and Files
        for tip_block in tips_related_blocks:

            internaltip_id = tip_block.get('internaltip')['internaltip_id']

            whistlebtip_iface.delete_access_by_itip(internaltip_id)
            receivertip_iface.massive_delete(internaltip_id)
            comment_iface.delete_comment_by_itip(internaltip_id)
            file_iface.delete_file_by_itip(internaltip_id)

            # and finally, delete the InternalTip
            internaltip_iface.tip_delete(internaltip_id)

        # (Just a consistency check - need to be removed)
        receiver_iface = Receiver(store)
        receivers_associated = receiver_iface.get_receivers_by_context(context_gus)
        print "receiver associated by context POV:", len(receivers_associated),\
        "receiver associated by context DB-field:", len(context_desc['receivers'])

        # Align all the receiver associated to the context, that the context cease to exist
        receiver_iface.align_context_delete(context_desc['receivers'], context_gus)

        # Get the profile list related to context_gus and delete all of them
        profile_iface = PluginProfiles(store)
        profile_list = profile_iface.get_profiles_by_contexts([ context_gus ])
        for prof in profile_list:
            profile_iface.delete_profile(prof['profile_gus'])

        # Get the submission list under the context, and delete all of them
        submission_iface = Submission(store)
        submission_list = submission_iface.get_all()
        for single_sub in submission_list:
            submission_iface.submission_delete(single_sub['submission_gus'])

        # Finally, delete the context
        context_iface.delete_context(context_gus)

        self.returnData(context_desc)
        self.returnCode(200)
        return self.returnValues()

    @transact
    def get_receiver_list(self):

        receiver_iface = Receiver(self.getStore())
        all_receivers = receiver_iface.get_all()

        self.returnData(all_receivers)
        self.returnCode(200)
        self.returnValues()

    @transact
    def create_receiver(self, request):

        store = self.getStore()

        receiver_iface = Receiver(store)

        new_receiver = receiver_iface.new(request)
        new_receiver_gus = new_receiver['receiver_gus']

        # 'contexts' it's a relationship between two tables, and is managed
        # with a separate method of new()
        context_iface = Context(store)
        receiver_iface.receiver_align(new_receiver_gus, request['contexts'])
        context_iface.full_context_align(new_receiver_gus, request['contexts'])

        new_receiver_desc = receiver_iface.get_single(new_receiver_gus)

        self.returnData(new_receiver_desc)
        self.returnCode(201)
        return self.returnValues()

    @transact
    def get_receiver(self, receiver_gus):

        receiver_iface = Receiver(self.getStore())
        receiver_description = receiver_iface.get_single(receiver_gus)

        self.returnData(receiver_description)
        self.returnCode(200)
        return self.returnValues()

    @transact
    def update_receiver(self, receiver_gus, request):

        store = self.getStore()

        receiver_iface = Receiver(store)
        receiver_iface.update(receiver_gus, request)

        # 'contexts' it's a relationship between two tables, and is managed
        # with a separate method of update()

        context_iface = Context(store)
        receiver_iface.receiver_align(receiver_gus, request['contexts'])
        context_iface.full_context_align(receiver_gus, request['contexts'])

        receiver_description = receiver_iface.get_single(receiver_gus)

        self.returnData(receiver_description)
        self.returnCode(200)
        return self.returnValues()

    @transact
    def delete_receiver(self, receiver_gus):

        store = self.getStore()

        receiver_iface = Receiver(store)
        receiver_desc = receiver_iface.get_single(receiver_gus)

        receivertip_iface = ReceiverTip()
        # Remove Tip possessed by the receiver
        related_tips = receivertip_iface.get_tips_by_receiver(receiver_gus)
        for tip in related_tips:
            receivertip_iface.personal_delete(tip['tip_gus'])
            # Remind: the comment are kept, and the name do not use a reference
            # but is stored in the comment entry.

        context_iface = Context(store)

        # Just an alignment check that need to be removed
        contexts_associated = context_iface.get_contexts_by_receiver(receiver_gus)
        print "context associated by receiver POV:", len(contexts_associated),\
        "context associated by receiver-DB field:", len(receiver_desc['contexts'])

        context_iface.align_receiver_delete(receiver_desc['contexts'], receiver_gus)

        receiverconf_iface = ReceiverConfs(store)
        receivercfg_list = receiverconf_iface.get_confs_by_receiver(receiver_gus)
        for rcfg in receivercfg_list:
            receiverconf_iface.delete(rcfg['config_id'], receiver_gus)

        # Finally delete the receiver
        receiver_iface.receiver_delete(receiver_gus)

        self.returnData(receiver_desc)
        self.returnCode(200)
        return self.returnValues()

    @transact
    def get_profile_list(self):

        profile_iface = PluginProfiles(self.getStore())
        all_profiles = profile_iface.get_all()

        self.returnData(all_profiles)
        self.returnCode(200)
        self.returnValues()

    @transact
    def create_profile(self, request):

        profile_iface = PluginProfiles(self.getStore())

        profile_description = profile_iface.new(request)

        self.returnData(profile_description)
        self.returnCode(201)
        self.returnValues()

