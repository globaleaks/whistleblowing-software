from globaleaks.transactors.base import MacroOperation

from globaleaks.models.node import Node
from globaleaks.models.context import Context
from globaleaks.models.receiver import Receiver
from globaleaks.models.externaltip import File, ReceiverTip, WhistleblowerTip, Comment
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.submission import Submission
from globaleaks.models.options import PluginProfiles, ReceiverConfs
from globaleaks.plugins.manager import PluginManager

from globaleaks.rest.errors import ForbiddenOperation, InvalidInputFormat

from storm.twisted.transact import transact

class CrudOperations(MacroOperation):
    """
    README.md describe pattern and reasons
    """

    # Below CrudOperations for Admin API

    @transact
    def get_node(self):

        node_iface = Node(self.getStore())
        node_description_dict = node_iface.get_single()

        self.returnData(node_description_dict)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def update_node(self, request):

        node_iface = Node(self.getStore())
        node_description_dict = node_iface.update(request)

        self.returnData(node_description_dict)
        self.returnCode(201)
        return self.prepareRetVals()

    @transact
    def get_context_list(self):

        context_iface = Context(self.getStore())
        all_contexts = context_iface.get_all()

        self.returnData(all_contexts)
        self.returnCode(200)
        return self.prepareRetVals()

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
        return self.prepareRetVals()


    @transact
    def get_context(self, context_gus):

        context_iface = Context(self.getStore())
        context_description = context_iface.get_single(context_gus)

        self.returnData(context_description)
        self.returnCode(200)
        return self.prepareRetVals()

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
        return self.prepareRetVals()

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
            submission_iface.submission_delete(single_sub['submission_gus'], wb_request=False)

        # Finally, delete the context
        context_iface.delete_context(context_gus)

        self.returnData(context_desc)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_receiver_list(self):

        receiver_iface = Receiver(self.getStore())
        all_receivers = receiver_iface.get_all()

        self.returnData(all_receivers)
        self.returnCode(200)
        return self.prepareRetVals()

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
        return self.prepareRetVals()

    @transact
    def get_receiver(self, receiver_gus):

        receiver_iface = Receiver(self.getStore())
        receiver_description = receiver_iface.get_single(receiver_gus)

        self.returnData(receiver_description)
        self.returnCode(200)
        return self.prepareRetVals()

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
        return self.prepareRetVals()

    @transact
    def delete_receiver(self, receiver_gus):

        store = self.getStore()

        receiver_iface = Receiver(store)
        receiver_desc = receiver_iface.get_single(receiver_gus)

        receivertip_iface = ReceiverTip(store)
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
        return self.prepareRetVals()

    @transact
    def get_profile_list(self):

        profile_iface = PluginProfiles(self.getStore())
        all_profiles = profile_iface.get_all()

        self.returnData(all_profiles)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def create_profile(self, request):

        profile_iface = PluginProfiles(self.getStore())

        profile_description = profile_iface.new(request)

        self.returnData(profile_description)
        self.returnCode(201)
        return self.prepareRetVals()

    @transact
    def get_profile(self, profile_gus):

        profile_iface = PluginProfiles(self.getStore())

        profile_description = profile_iface.get_single(profile_gus)

        self.returnData(profile_description)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def update_profile(self, profile_gus, request):

        profile_iface = PluginProfiles(self.getStore())

        profile_description = profile_iface.update(profile_gus, request)

        self.returnData(profile_description)
        self.returnCode(201)
        return self.prepareRetVals()

    @transact
    def delete_profile(self, profile_gus):

        profile_iface = PluginProfiles(self.getStore())

        profile_description = profile_iface.get_single(profile_gus)
        profile_iface.delete_profile(profile_gus)

        self.returnData(profile_description)
        self.returnCode(200)
        return self.prepareRetVals()

    # Completed CrudOperations for the Admin API
    # Below CrudOperations for Receiver API

    @transact
    def get_receiver_by_receiver(self, valid_tip):

        receivertip_iface = ReceiverTip(self.getStore())

        receivers_map = receivertip_iface.get_receivers_by_tip(valid_tip)
        # receivers_map is a dict with these keys: 'others' : [$], 'actor': $, 'mapped' [ ]

        self.returnData(receivers_map['actor'])
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def update_receiver_by_receiver(self, valid_tip, request):

        store = self.getStore()
        receivertip_iface = ReceiverTip(store)

        receivers_map = receivertip_iface.get_receivers_by_tip(valid_tip)
        # receivers_map is a dict with these keys: 'others' : [$], 'actor': $, 'mapped' [ ]

        self_receiver_gus = receivers_map['actor']['receiver_gus']

        receiver_iface = Receiver(store)
        receiver_desc = receiver_iface.self_update(self_receiver_gus, request)

        # context_iface = Context(store)
        # context_iface.update_languages(receiver_desc['contexts'])
        # TODO implement this function

        self.returnData(receiver_desc)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_profiles_by_receiver(self, valid_tip):

        store = self.getStore()
        receivertip_iface = ReceiverTip(store)
        receivers_map = receivertip_iface.get_receivers_by_tip(valid_tip)
        # receivers_map is a dict with these keys: 'others' : [$], 'actor': $, 'mapped' [ ]

        receiver_associated_contexts = receivers_map['actor']['contexts']

        profile_iface = PluginProfiles(store)
        profiles_list = profile_iface.get_profiles_by_contexts(receiver_associated_contexts)

        self.returnData(profiles_list)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_receiversetting_list(self, valid_tip):

        store = self.getStore()

        receivertip_iface = ReceiverTip(store)
        receivers_map = receivertip_iface.get_receivers_by_tip(valid_tip)

        user = receivers_map['actor']

        receivercfg_iface = ReceiverConfs(store)
        confs_created = receivercfg_iface.get_confs_by_receiver(user['receiver_gus'])

        self.returnData(confs_created)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def new_receiversetting(self, valid_tip, request):

        store = self.getStore()

        receivertip_iface = ReceiverTip(store)

        receivers_map = receivertip_iface.get_receivers_by_tip(valid_tip)
        user = receivers_map['actor']

        profile_iface = PluginProfiles(store)
        profile_desc = profile_iface.get_single(request['profile_gus'])

        if profile_desc['plugin_type'] == u'notification' and user['can_configure_notification']:
            pass
        elif profile_desc['plugin_type'] == u'delivery' and user['can_configure_delivery']:
            pass
        else:
            raise ForbiddenOperation

        receivercfg_iface = ReceiverConfs(store)
        config_desc = receivercfg_iface.new(user['receiver_gus'], request)

        if config_desc['active']:
            # keeping active only the last configuration requested
            receivercfg_iface.deactivate_all_but(config_desc['config_id'], config_desc['context_gus'],
                user['receiver_gus'], config_desc['plugin_type'])

        self.returnData(config_desc)
        self.returnCode(201)
        return self.prepareRetVals()

    @transact
    def get_receiversetting(self, valid_tip, conf_id):

        store = self.getStore()

        # This check verify if auth is correct
        receivertip_iface = ReceiverTip(store)
        receivers_map = receivertip_iface.get_receivers_by_tip(valid_tip)

        # This one in fact return the Receiver Setting requested
        receivercfg_iface = ReceiverConfs(store)
        conf_requested = receivercfg_iface.get_single(conf_id)

        self.returnData(conf_requested)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def update_receiversetting(self, valid_tip, conf_id, request):

        store = self.getStore()

        receivertip_iface = ReceiverTip(store)
        receivers_map = receivertip_iface.get_receivers_by_tip(valid_tip)
        user = receivers_map['actor']

        profile_iface = PluginProfiles(store)
        profile_desc = profile_iface.get_single(request['profile_gus'])

        if profile_desc['plugin_type'] == u'notification' and user['can_configure_notification']:
            pass
        elif profile_desc['plugin_type'] == u'delivery' and user['can_configure_delivery']:
            pass
        else:
            raise ForbiddenOperation

        receivercfg_iface = ReceiverConfs(store)
        config_update = receivercfg_iface.update(conf_id, user['receiver_gus'], request)

        if config_update['active']:
            # keeping active only the last configuration requested
            receivercfg_iface.deactivate_all_but(config_update['config_id'], config_update['context_gus'],
                user['receiver_gus'], config_update['plugin_type'])

        self.returnData(config_update)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def delete_receiversetting(self, valid_tip, conf_id):

        store = self.getStore()

        receivertip_iface = ReceiverTip(store)
        receivers_map = receivertip_iface.get_receivers_by_tip(valid_tip)
        user = receivers_map['actor']

        receivercfg_iface = ReceiverConfs(store)
        receivercfg_iface.delete(conf_id, user['receiver_gus'])

        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_tip_list(self, valid_tip):

        store = self.getStore()
        receivertip_iface = ReceiverTip(store)

        tips = receivertip_iface.get_tips_by_tip(valid_tip)
        # this function return a dict with: { 'othertips': [$rtip], 'request' : $rtip }

        tips['othertips'].append(tips['request'])

        self.returnData(tips)
        self.returnCode(200)
        return self.prepareRetVals()

    # Completed CrudOperations for the Receiver API
    # Below CrudOperations for Tip API

    @transact
    def get_tip_by_receiver(self, tip_gus):

        requested_t = ReceiverTip(self.getStore())
        tip_description = requested_t.get_single(tip_gus)

        self.returnData(tip_description)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_tip_by_wb(self, receipt):

        requested_t = WhistleblowerTip(self.getStore())
        tip_description = requested_t.get_single(receipt)

        self.returnData(tip_description)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def update_tip_by_receiver(self, tip_gus, request):

        store = self.getStore()

        receivertip_iface = ReceiverTip(store)

        if request['personal_delete']:
            receivertip_iface.personal_delete(tip_gus)

        elif request['is_pertinent']:
            # elif is used to avoid the message with both delete+pertinence.
            # This operation is based in ReceiverTip and is returned
            # the sum of the vote expressed. This value is updated in InternalTip
            (itip_id, vote_sum) = receivertip_iface.pertinence_vote(tip_gus, request['is_pertinent'])

            internaltip_iface = InternalTip(store)
            internaltip_iface.update_pertinence(itip_id, vote_sum)

        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def delete_tip(self, tip_gus):

        store = self.getStore()

        receivertip_iface = ReceiverTip(store)

        receivers_map = receivertip_iface.get_receivers_by_tip(tip_gus)

        if not receivers_map['actor']['can_delete_submission']:
            raise ForbiddenOperation

        # sibilings_tips has the keys: 'sibilings': [$] 'requested': $
        sibilings_tips = receivertip_iface.get_sibiligs_by_tip(tip_gus)

        # delete all the related tip
        for sibiltip in sibilings_tips['sibilings']:
            receivertip_iface.personal_delete(sibiltip['tip_gus'])

        # and the tip of the called
        receivertip_iface.personal_delete(sibilings_tips['requested']['tip_gus'])

        # extract the internaltip_id, we need for the next operations
        itip_id = sibilings_tips['requested']['internaltip_id']

        # remove all the files: XXX think if delivery method need to be inquired
        file_iface = File(store)
        files_list = file_iface.get_files_by_itip(itip_id)

        # remove all the comments based on a specific itip_id
        comment_iface = Comment(store)
        comments_list = comment_iface.delete_comment_by_itip(itip_id)

        internaltip_iface = InternalTip(store)
        # finally, delete the internaltip
        internaltip_iface.tip_delete(sibilings_tips['requested']['internaltip_id'])

        # XXX Notify Tip removal to the receivers ?
        # XXX ask to the deleter a comment about the action, notifiy this comment ?

        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_comment_list_by_receiver(self, tip_gus):

        store = self.getStore()

        requested_t = ReceiverTip(store)
        tip_description = requested_t.get_single(tip_gus)

        comment_iface = Comment(store)
        comment_list = comment_iface.get_comment_by_itip(tip_description['internaltip_id'])

        self.returnData(comment_list)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_comment_list_by_wb(self, receipt):

        store = self.getStore()

        requested_t = WhistleblowerTip(store)
        tip_description = requested_t.get_single(receipt)

        comment_iface = Comment(store)
        comment_list = comment_iface.get_comment_by_itip(tip_description['internaltip_id'])

        self.returnData(comment_list)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def new_comment_by_receiver(self, tip_gus, request):

        store = self.getStore()

        requested_t = ReceiverTip(store)
        tip_description = requested_t.get_single(tip_gus)

        comment_iface = Comment(store)

        comment_stored = comment_iface.new(tip_description['internaltip_id'],
            request['content'], u"receiver", tip_description['receiver_gus'])
        # XXX here can be put the name of the Receiver

        self.returnData(comment_stored)
        self.returnCode(201)
        return self.prepareRetVals()

    @transact
    def new_comment_by_wb(self, receipt, request):

        store = self.getStore()

        requested_t = WhistleblowerTip(store)
        tip_description = requested_t.get_single(receipt)

        comment_iface = Comment(store)

        comment_stored = comment_iface.new(tip_description['internaltip_id'],
            request['content'], u"whistleblower")

        self.returnData(comment_stored)
        self.returnCode(201)
        return self.prepareRetVals()


    @transact
    def get_receiver_list_by_receiver(self, tip_gus):

        store = self.getStore()

        requested_t = ReceiverTip(store)
        tip_description = requested_t.get_single(tip_gus)

        itip_iface = InternalTip(store)
        inforet = itip_iface.get_receivers_by_itip(tip_description['internaltip_id'])

        self.returnData(inforet)
        self.returnCode(200)
        return self.prepareRetVals()

    @transact
    def get_receiver_list_by_wb(self, receipt):

        store = self.getStore()

        requested_t = WhistleblowerTip(store)
        tip_description = requested_t.get_single(receipt)

        itip_iface = InternalTip(store)
        # inforet = itip_iface.get_receivers_by_itip(tip_description['internaltip_id'])
        # the wb, instead get the list of active receiver, is getting the list of receiver
        # configured in the context:
        inforet = itip_iface.get_single(tip_description['internaltip_id'])['receivers']

        self.returnData(inforet)
        self.returnCode(200)
        return self.prepareRetVals()

    # Completed CrudOperations for the Tip API
    # Below CrudOperations for Submission API

    @transact
    def new_submission(self, request):

        store = self.getStore()

        context_desc = Context(store).get_single(request['context_gus'])

        if not context_desc['selectable_receiver']:
            request.update({'receivers' : context_desc['receivers'] })

        submission_desc = Submission(store).new(request)

        if submission_desc['finalize']:

            internaltip_desc =  InternalTip(store).new(submission_desc)

            wbtip_desc = WhistleblowerTip(store).new(internaltip_desc)

            submission_desc.update({'receipt' : wbtip_desc['receipt']})
        else:
            submission_desc.update({'receipt' : ''})

        self.returnData(submission_desc)
        self.returnCode(201) # Created
        return self.prepareRetVals()

    @transact
    def get_submission(self, submission_gus):

        store = self.getStore()

        submission_desc = Submission(store).get_single(submission_gus)

        self.returnData(submission_desc)
        self.returnCode(201) # Created
        return self.prepareRetVals()

    @transact
    def update_submission(self, submission_gus, request):

        store = self.getStore()

        context_desc = Context(store).get_single(request['context_gus'])

        if not context_desc['selectable_receiver']:
            request.update({'receivers' : context_desc['receivers'] })

        submission_desc = Submission(store).update(submission_gus, request)

        if submission_desc['finalize']:

            internaltip_desc =  InternalTip(store).new(submission_desc)

            wbtip_desc = WhistleblowerTip(store).new(internaltip_desc)

            submission_desc.update({'receipt' : wbtip_desc['receipt']})
        else:
            submission_desc.update({'receipt' : ''})

        self.returnData(submission_desc)
        self.returnCode(202) # Updated
        return self.prepareRetVals()

    @transact
    def delete_submission(self, submission_gus):

        store = self.getStore()
        Submission(store).submission_delete(submission_gus, wb_request=True)

        self.returnCode(200)
        return self.prepareRetVals()

    # Completed CrudOperations for the Submission API
    # Below CrudOperations for Debug API

    @transact
    def dump_models(self, expected):

        expected_dict = { 'itip' : InternalTip,
                          'wtip' : WhistleblowerTip,
                          'rtip' : ReceiverTip,
                          'receivers' : Receiver,
                          'comment' : Comment,
                          'profiles' : PluginProfiles,
                          'rcfg' : ReceiverConfs,
                          'file' : File,
                          'submission' : Submission,
                          'contexts' : Context }

        outputDict = {}
        self.returnCode(200)

        store = self.getStore()

        if expected in ['count', 'all']:

            for key, object in expected_dict.iteritems():
                info_list = object(store).get_all()

                if expected == 'all':
                    outputDict.update({key : info_list})

                outputDict.update({("%s_elements" % key) : len(info_list) })

            self.returnData(outputDict)
            return self.prepareRetVals()

        # XXX plugins is not dumped with all or count!
        if expected == 'plugins':

            info_list = PluginManager.get_all()
            outputDict.update({expected : info_list, ("%s_elements" % expected) : len(info_list) })

            self.returnData(outputDict)
            return self.prepareRetVals()

        if expected_dict.has_key(expected):

            info_list = expected_dict[expected](store).get_all()
            outputDict.update({expected : info_list, ("%s_elements" % expected) : len(info_list) })

            self.returnData(outputDict)
            return self.prepareRetVals()

        raise InvalidInputFormat("Not acceptable '%s'" % expected)




