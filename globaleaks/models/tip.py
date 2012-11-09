# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE
from storm.exceptions import NotOneError

from storm.twisted.transact import transact
from storm.locals import Int, Pickle, Date, Unicode, RawStr, Bool, DateTime
from storm.locals import Reference, ReferenceSet

# under the voce of "needlessy overcomplications", Twister + Storm
# http://twistedmatrix.com/users/radix/storm-api/storm.store.ResultSet.html
from globaleaks.utils import idops, log, gltime

from globaleaks.models.base import TXModel, ModelError
from globaleaks.models.receiver import Receiver
from globaleaks.models.context import Context

from globaleaks.messages.responses import errorMessage

__all__ = [ 'InternalTip', 'Folder', 'File', 'Comment',
            'ReceiverTip', 'PublicStats', 'WhistleblowerTip' ]

class TipModelError(ModelError):
    log.debug("[D] %s %s " % (__file__, __name__), "Class TipModelError", "ModelError", ModelError)
    pass

class TipNotFoundError(TipModelError):
    log.debug("[D] %s %s " % (__file__, __name__), "Class TipNotFoundError", "TipModelError", TipModelError)
    pass

class Folder(TXModel):
    """
    This represents a file set: a collection of files, description, time
    Every receiver has a different Folder, and if more folder exists, the
    number of folder is (R * Folder_N).
    This is the unique way we had to ensure end to end encryption WB-receiver,
    and if uncrypted situation, simply the Files referenced here are also
    referenced in the other Folders.
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Folder", "TXModel", TXModel)
    __storm_table__ = 'folders'

    folder_gus = Unicode(primary=True)

    name = Unicode()
    description = Unicode()

    property_applied = Pickle()
    # actually there are not property, but here would be marked if symmetric
    # asymmetric encryption has been used.

    upload_time = Date()

    # to be expanded in the near future XXX
    # at the moment, folder is not associated to a receiver
    #  associated_receiver_id = Int()
    #  associated_receiver = Reference(associated_receiver_id, Receiver.id)
    # associated_receiver_id is useful for show, in the general page of the
    # receiver, eventually the latest available folders

    internaltip_id = Int()
    # internaltip = Reference(internaltip_id, InternalTip.id)
    # GLBackend/globaleaks/models/tip.py", line 67, in Folder
    # internaltip = Reference(internaltip_id, InternalTip.id)
    # NameError: name 'InternalTip' is not defined
    # -- then, I moved that line after InternalTip


def file_dicts(self):
        file_dicts = []
        log.debug("Processing %s" % self.files)
        for f in self.files:
            log.debug("Generating file dict")
            print "In here y0 %s" % f
            file_dict = {'name': f.name,
                    'description': f.description,
                    'size': f.size,
                    'content_type': f.content_type,
                    'date': f.uploaded_date,
                    'metadata_cleaned': f.metadata_cleaned,
                    'completed': f.completed}
            log.debug("Done %s" % file_dict)
            file_dicts.append(file_dict)
        return file_dicts


class File(TXModel):
    """
    The file are *stored* here, along with their properties
    """
    log.debug("[D] %s %s " % (__file__, __name__), "File", "TXModel", TXModel)
    __storm_table__ = 'files'

    file_gus = Unicode(primary=True)

    name = Unicode()
    content = RawStr()

    completed = Bool()

    shasum = RawStr()

    description = Unicode()
    content_type = Unicode()

    size = Int()

    metadata_cleaned = Bool()
    uploaded_date = Date()

    folder_gus = Unicode()
    folder = Reference(folder_gus, Folder.folder_gus)

Folder.files = ReferenceSet(Folder.folder_gus, File.folder_gus)

class Comment(TXModel):
    log.debug("[D] %s %s " % (__file__, __name__), "Comment", "TXModel", TXModel)
    __storm_table__ = 'comments'

    id = Int(primary=True)

    type = Unicode()
    content = Unicode()
    author = Unicode()
    comment_date = Date()

    internaltip_id = Int()
    # internaltip = Reference(internaltip_id, InternalTip.id)
    # GLBackend/globaleaks/models/tip.py", line 133, in Comment
    # internaltip = Reference(internaltip_id, InternalTip.id)
    # NameError: name 'InternalTip' is not defined
    # -- then, I moved that line after InternalTip decl


class InternalTip(TXModel):
    """
    This is the internal representation of a Tip that has been submitted to the
    GlobaLeaks node.

    It has a not associated map for keep track of Receivers, Tips, Folders,
    Comments and WhistleblowerTip.
    All of those element has a Storm Reference with the InternalTip.id, not
    vice-versa

    Every tip has a certain shared data between all, and they are here collected
    """
    log.debug("[D] %s %s " % (__file__, __name__), "InternalTip", "TXModel", TXModel)
    __storm_table__ = 'internaltips'

    id = Int(primary=True)

    fields = Pickle()
    pertinence_counter = Int()
    escalation_threshold = Int()
    creation_date = Date()
    expiration_date = Date()

    # the LIMITS are defined and declared *here*, and track in
    # ReceiverTip (access) and Folders (download, if delivery supports)
    access_limit = Int()
    download_limit = Int()

    mark = Unicode()
        # TODO ENUM: new, first, second

    receivers_map = Pickle()

    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)

        # Both to be cleaned and uniformed
    comments = Pickle()
    folders = ReferenceSet(id, Folder.internaltip_id)
        # remind: I've removed file reference from InternalTip
        # because do not exists file leaved alone
    comments = ReferenceSet(id, Comment.internaltip_id)

    # called by a transact: submission.complete_submission
    def initialize(self, submission):
        """
        initialized an internalTip having the context
        @return: none
        """
        self.creation_date = gltime.utcDateNow()
        self.context_gus = submission.context.context_gus
        self.context = submission.context
        self.escalation_threshold = submission.context.escalation_threshold
        self.access_limit = submission.context.tip_max_access
        self.expiration_date = submission.expiration_time
        self.fields = submission.fields
        self.pertinence_counter = 0
        self.download_limit = submission.context.folder_max_download
        self.receivers_map = []
        self.mark = u'new'
        # all the fields copied by context, can by logic be
        # obtained via InternalTip.context, but this kind of
        # optimization I prefer is done when code is barely stable :P

    # called by a transact: submission.complete_submission
    def associate_receiver(self, chosen_r):

        self.receivers_map.append({
            'receiver_gus' : chosen_r.receiver_gus,
            'receiver_level' : chosen_r.receiver_level,
            'tip_gus' : None,
            'notification_selected' : chosen_r.notification_selected,
            'notification_fields' : chosen_r.notification_fields  })

        log.debug("associate_receiver, called by complete_submission", self.receivers_map)

    # perhaps get_newly_generated and get_newly_escalated can be melted
    @transact
    def get_newly_generated(self):
        """
        @return: all the internaltips with mark == u'new', in a list of id
        """
        store = self.getStore('get_newly_generated')

        new_itips = store.find(InternalTip, InternalTip.mark == u'new')

        retVal = []
        for single_itip in new_itips:
            retVal.append(single_itip.id)

        store.close()
        return retVal

    @transact
    def get_newly_escalated(self):
        """
        @return: all the internaltips with pertinence_counter >= escalation_threshold and mark == u'first',
            in a list of id
        """
        #store = self.getStore('get_newly_escalated')
        #store.close()
        return {}

    @transact
    def flip_mark(self, subject_id, newmark):
        """
        @param newmark: u'first' or u'second'
        @subject_id: InternalTip.id to be changed
        @return: None
        """
        store = self.getStore('flip mark')

        requested_t = store.find(InternalTip, InternalTip.id == subject_id).one()
        requested_t.mark = newmark

        store.commit()
        store.close()

    # This method is separated by initialize routine, because in a certain future
    # would be exported outside of InternalTip and implemented in a module, like
    # notification or delivery
    @transact
    def create_receiver_tips(self, id, tier):
        """
        act on self. create the ReceiverTip based on self.receivers_map
        """
        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip create_receiver_tips", id, "on tier", tier)

        store = self.getStore('create_receiver_tips')

        selected_it = store.find(InternalTip, InternalTip.id == id).one()

        for i, mapped in enumerate(selected_it.receivers_map):

            if not mapped['receiver_level'] == tier:
                continue

            receiver_subject = store.find(Receiver, Receiver.receiver_gus == selected_it.receivers_map[i]['receiver_gus']).one()

            receiver_tip = ReceiverTip()

            # is initialized a Tip that need to be notified
            receiver_tip.initialize(mapped, selected_it, receiver_subject)

            receiver_subject.update_timings()

            selected_it.receivers_map[i]['tip_gus'] = receiver_tip.tip_gus
            store.add(receiver_tip)

        # commit InternalTip.receivers_map[only requested tier]['tip_gus'] & ReceiverTip(s)
        store.commit()
        store.close()

    @transact
    def admin_get_all(self):

        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip admin_print_all")

        store = self.getStore('admin_print_all')
        all_itips = store.find(InternalTip)

        retVal = []
        for itip in all_itips:
            retVal.append(itip._description_dict() )

        store.close()
        return retVal

    def _description_dict(self):

        description_dict = {
            'id' : self.id,
            'context_ref' : [ self.context.name, self.context_gus ],
            'creation_date' : gltime.prettyDateTime(self.creation_date),
            'expiration_date' : gltime.prettyDateTime(self.creation_date),
            'fields' : self.fields,
            'pertinence' : self.pertinence_counter,
            'download_limit' : self.download_limit,
            'access_limit' : self.access_limit,
            'mark' : self.mark,
            'receiver_map' : self.receivers_map # it's already a dict
        }
        return description_dict

    # ----------------------------------------------------
    # -- ALL BELOW NEED TO BE REFACTORED WITH THE DELIVERY
    #
    def folder_dicts(self):
        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip", "folder_dicts")
        folder_dicts = []
        for folder in self.folders:
            folder_dict = {'name': folder.name,
                    'description': folder.description,
                    # 'downloads': self.downloads, # downloads need to be tracked in Folder
                    'files': folder.file_dicts()}
            folder_dicts.append(folder_dict)
        return folder_dicts

    def postpone_expiration(self):
        """
        function called when a receiver has this option
        """
        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip", "postpone_expiration")

    def tip_total_delete(self):
        """
        function called when a receiver choose to remove a submission
        and all the derived tips. is called by scheduler when
        timeoftheday is >= expired_date
        """
        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip", "tip_total_delete")

Folder.internaltip = Reference(Folder.internaltip_id, InternalTip.id)
Comment.internaltip = Reference(Comment.internaltip_id, InternalTip.id)



class Tip(TXModel):
    log.debug("[D] %s %s " % (__file__, __name__), "Class Tip", "TXModel", TXModel)
    __storm_table__ = 'tips'

    # remind: the previous name of this variable was 'address'
    tip_gus = Unicode(primary=True)

    type = Unicode()
    password = Unicode()

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)

    @transact
    def get_all_admin(self):
        """
        @return: all Receivers Tip, printed by 'overview' admin API
        """

    @transact
    def get_all_receiver(self, tip_gus):
        """
        @param tip_gus: get all the tip for the receiver auth with a valid tip_gus
        @return: the simpler index, used as tip list
        """

    @transact
    def get_single_receiver(self, tip_gus):
        # is the lookup
        pass

    # need totally to be refactored, and partially implemented in InternalTip
    def get_sub_index(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Tip", "get_sub_index")
        ret = {
            #"notification_adopted": unicode,
            #"delivery_adopted": unicode,
            "download_limit": self.internaltip.download_limit,
            # remind: download_performed is inside the folderDict
            "access_limit": self.internaltip.access_limit,
            #"access_performed": self.,
            "expiration_date": gltime.prettyDateTime(self.internaltip.expiration_date),
            "creation_date": gltime.prettyDateTime(self.internaltip.creation_date),
            #"last_update_date": self.internaltip.last_update_date,
            # "comment_number": len(list(self.internaltip.comments)),
            # "folder_number": len(list(self.internaltip.folders)),
            "pertinence": self.internaltip.pertinence_counter
        }
        return ret

    #  ----------------
    # NEED TO BE REFACTORED
    @transact
    def lookup(self, receipt):
        """
        receipt actually is either a random_tip_gus and a random_receipt_gus,
        in the future, would be the hash of a random_receipt_gus.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Tip", "lookup", "receipt", receipt )
        store = self.getStore('lookup')

        tip = store.find(Tip, Tip.tip_gus == receipt).one()
        if not tip:
            store.rollback()
            store.close()
            raise TipNotFoundError

        tip_sub_index = tip.get_sub_index()

        folders = tip.internaltip.folders
        # ANSWERED folders do not exist in the Tip variables, why ?
        # + folders shall not be downloaded by the WB, this info can be stripped
        # off the folder_gus (required to download)
        #
        # As mentioned on IRC for the moment we want to keep it simple and not
        # have a folder per receiver.
        # Once we will have the functionality to add the settings that
        # distinguish the folders based on the receiver we will change the
        # folders here to do a lookup on folders for the tip that is specific
        # to this receiver

        comments = tip.internaltip.comments
        # ANSWERED comments do not exist in the Tip variables, why ?
        # They are not properties of the Tip variable, but of the internal tip.
        # The comments are currently global to every tip.

        context = tip.internaltip.context_gus

        receiver_dicts = tip.internaltip.context.receiver_dicts()
        folders = tip.internaltip.folder_dicts()

        tip_details = {'tip': tip_sub_index,
                   'fields': tip.internaltip.fields,
                   'folders': folders,#folders,
                   'comments': None, #comments,
                   'context': context,
                   'receivers': receiver_dicts
        }
        store.commit()
        store.close()

        return tip_details


class ReceiverTip(Tip):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """

    authoptions = Pickle()
        # this can be a security expansion to be evaluated, actually ther
        # password checks in the tip, is only one for Receiver, and is stored
        # in Receiver

    access_counter = Int()
    last_access = Date()

    relative_view_count = Int()
        # wtf would be relative view count ? the checks that if a comment
        # or update is present, than the number of view count is incremented ?
        # in this case, is much more sane keeping track in InternalTip, inside
        # of the max_access_counter. but this automatized escalation can bring to
        # abuse. I don't feel is the right solution and we need to make a little
        # analysis before implement it.

    relative_download_count = Int()
        # TODO all the download ref need to be removed an moved in Folder
        # the max amount of download is tracked in InternalTip
        # what about free speech mr president ? http://www.youtube.com/watch?v=MokNvbiRqCM

    pertinence_vote = Int()

    notification_date = DateTime()
    notification_mark = Unicode()
        # TODO ENUM 'not notified' 'notified' 'unable to notify' 'notification ignore'

    receiver_gus = Unicode()
    receiver = Reference(receiver_gus, Receiver.receiver_gus)

    # is not a transact operation, just a self filling
    def initialize(self, mapped, selected_it, receiver_subject):

        log.debug("ReceverTip initialize, with", mapped)
        print "initialize with", mapped

        self.tip_gus = idops.random_tip_gus()

        self.notification_mark = u'not notified'

        self.notification_date = None
        self.last_access = None
        self.access_counter= 0
        self.pertinence_vote = 0
        self.authoptions = {}

        self.receiver_gus = mapped['receiver_gus']
        self.receiver = receiver_subject

        # 'notification_selected'
        # 'notification_fields'
        # XXX shall be reached by self.receiver, evaluate if remove
        # from receiver_map


    # This would be moved in the new 'task queue'
    @transact
    def get_tips(self, status=None):
        """
        @param status: unicode!
        @return:
        """
        store = self.getStore('get_tips')

        notification_status = [ u'not notified', u'notified', u'unable to notify', u'notification ignore' ]
        if not status in notification_status:
            raise Exception("Invalid developer brain dictionary")

        # TODO ENUM 'not notified' 'notified' 'unable to notify' 'notification ignore'
        marked_tips = store.find(ReceiverTip, ReceiverTip.mark == status)

        retVal = {}
        for single_tip in marked_tips:
            retVal.update({
                'notification_fields' : single_tip.receiver.notification_fields,
                'notification_selected' : single_tip.receiver.notification_selected,
                'tip_gus' : single_tip.tip_gus
            })

        store.close()

        return retVal

    @transact
    def admin_get_all(self):

        store = self.getStore('receiver tips - admin_get_all')

        all_rt = store.find(ReceiverTip)

        retVal = []
        for single_rt in all_rt:
            retVal.append(single_rt._description_dict())

        store.close()
        return retVal

    # called by a transact operation, dump the ReceiverTip
    def _description_dict(self):

        descriptionDict = {
            'internaltip_id' : self.internaltip_id,
            'tip_gus' : self.tip_gus,
            'notification_mark' : self.notification_mark,
            'notification_date' : gltime.prettyDateTime(self.notification_date),
            'last_access' : gltime.prettyDateTime(self.last_access),
            'access_counter' : self.access_counter,
            'pertinence_vote': self.pertinence_vote,
            'receiver_gus' : self.receiver_gus,
            'authoptions' : self.authoptions
        }
        return descriptionDict


    # Perhaps to be moved in InternalTip XXX
    @transact
    def add_comment(self, tip_gus, comment):
        """
        From a Tip hook the internalTip, and update comments inside.
        comment_type and name of the author need to be written at the commit
        time, and not when comments are show to the users (perhaps, some user would
        remove a tip, breaking reference. this separation it's required for that).
        comment_type of those comments is "receiver" (other are "whistleblower" and
        "system")
        """
        log.debug("[D] %s %s " % (__file__, __name__), "ReceiverTip class", "add_comment", "tip_gus", tip_gus, "comment", comment)
        store = self.getStore('add_comment')

        try:
            # XXX - aarrgghh - naming refactor remind!
            tip = store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        except NotOneError, e:
            log.err("add_comment (receiver side): Problem looking up %s" % tip_gus)
            store.rollback()
            store.close()
            raise TipNotFoundError

        if not tip:
            store.rollback()
            store.close()
            raise TipNotFoundError

        newcomment = Comment()
        newcomment.internaltip_id = tip.internaltip.id
        newcomment.type = u"receiver" # XXX its commentENUM
        newcomment.content = comment

        print "debug 1", type(tip.receiver)
        print "debug 2", type(tip.receiver_gus)
        newcomment.author = u'temp fake name'

        store.add(newcomment)
        store.commit()
        store.close()


class WhistleblowerTip(Tip):
    """
    WhisteleblowerTip is intended, at the moment, to provide a whistleblower access to the Tip.
    differently from the ReceiverTips, has a secret and/or authentication checks, has
    different capabilities, like: cannot not download, cannot express pertinence, and
    other operation permitted to the WB shall be configured by the Admin.

    SpecialTip contains some information, but the tip data returned to the WB, is
    composed by SpecialTip + Tip
    """

    """
    need to have a tip_US (unique string) ? may even not, in fact, in the 0.1 release
    we had used a tip_US just because was stored in the same table, but if we support
    a more complex auth system for the whistleblower, we want that WB come back
    to the tip only using this method, not using /tip/<t_US> like a receiver.

    This is the reason because here is not placed a t_US, but just a secret
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class WhistleblowerTip")
    secret = Pickle()

    # XXX we probably don't want to store this stuff for the WB receipt.
    #     we may just want to store the last_access count, but properly
    #     anonymize it, like only store the fact that they logged in in the
    #     last week. So store just a week number.
    #view_count = Int()
    #last_access = Date()

    @transact
    def admin_get_all(self):

        store = self.getStore('wb_tips - admin_get_all')

        all_wt = store.find(WhistleblowerTip)

        retVal = []
        for single_wt in all_wt:
            retVal.append(single_wt._description_dict())

        store.close()
        return retVal

    # called by a transact operation, dump the WhistleBlower Tip
    def _description_dict(self):

        descriptionDict = {
            'internaltip_id' : self.internaltip_id,
            'tip_gus' : self.tip_gus
            # 'secret' : self.secret
        }
        return descriptionDict


class PublicStats(TXModel):
    """
    * Follow the same logic of admin.AdminStats,
    * need to be organized along with the information that we want to shared to the WBs:
       *  active_submission represent the amount of submission active in the moment
       *  node activities is a sum of admin + receiver operation
    * that's all time dependent information
       * remind: maybe also non-time dependent information would exists, if a node want to publish also their own analyzed submission, (but this would require another db table)
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class PublicStats")
    __storm_table__ = 'publicstats'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, active_submissions INT, node_activities INT, uptime INT"

    id = Int(primary=True)

    active_submissions = Int()
    node_activities = Int()
    uptime = Int()
    """
    likely would be expanded, but avoiding to spread information that may lead an attacker advantaged
    """


"""
The classic tip stay in receiver.ReceiverTip
"""
