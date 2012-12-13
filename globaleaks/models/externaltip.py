# -*- coding: UTF-8
#
#   models/externaltip
#   ******************
#
# implementatin of Storm DB side of ReceiverTip and WhistleblowerTip
# and File and Comment tables, all those tables has relationship with
# InternalTip

from storm.twisted.transact import transact
from storm.exceptions import NotOneError
from storm.locals import Int, Pickle, Date, Unicode, RawStr, Bool, DateTime
from storm.locals import Reference, ReferenceSet

from globaleaks.utils import idops, log, gltime
from globaleaks.models.base import TXModel, ModelError
from globaleaks.models.receiver import Receiver
from globaleaks.models.internaltip import InternalTip

__all__ = [ 'Folder', 'File', 'Comment', 'ReceiverTip', 'PublicStats', 'WhistleblowerTip',
            'TipGusNotFoundError', 'TipReceiptNotFoundError', 'TipPertinenceExpressed' ]

class TipGusNotFoundError(ModelError):

    def __init__(self):
        ModelError.error_message = "Invalid Globaleask Unique String referred to a Tip"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 400 # Bad Request

class TipReceiptNotFoundError(ModelError):

    def __init__(self):
        ModelError.error_message = "The inserted receipt do not exists in GlobaLeaks"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 400 # Bad Request

class TipPertinenceExpressed(ModelError):

    def __init__(self):
        ModelError.error_message = "Pertinence evaluation has been already expressed"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 406 # Conflict

class ReceiverTip(TXModel):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    __storm_table__ = 'receivertips'

    # remind: the previous name of this variable was 'address'
    tip_gus = Unicode(primary=True)

    authoptions = Pickle()

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)

    access_counter = Int()
    last_access = DateTime()

    expressed_pertinence = Int()

    notification_date = DateTime()
    notification_mark = Unicode()
        # TODO ENUM 'not notified' 'notified' 'unable to notify' 'notification ignore'

    receiver_gus = Unicode()
    receiver = Reference(receiver_gus, Receiver.receiver_gus)

    # is not a transact operation, is self filling,
    # called by InternalTip.create_receiver_tips
    def initialize(self, mapped, selected_it, receiver_subject):

        log.debug("ReceverTip initialize, with", mapped)
        self.tip_gus = idops.random_tip_gus()

        self.notification_mark = u'not notified'
        self.notification_date = None

        self.last_access = None
        self.access_counter= 0
        self.expressed_pertinence = 0
        self.authoptions = {}

        self.receiver_gus = mapped['receiver_gus']
        self.receiver = receiver_subject

        self.internaltip_id = selected_it.id
        self.internaltip = selected_it


    # XXX This would be moved in the new 'task queue', it's a get_tips_by_marker
    @transact
    def get_tips(self, marker=None):
        """
        @param status: unicode!
        @return:
        """
        store = self.getStore('get_tips')

        notification_markers = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]
        if not marker in notification_markers:
            raise Exception("Invalid developer brain dictionary", marker)

        # XXX ENUM 'not notified' 'notified' 'unable to notify' 'notification ignore'
        marked_tips = store.find(ReceiverTip, ReceiverTip.notification_mark == marker)

        retVal = []
        for single_tip in marked_tips:
            retVal.append({
                'notification_fields' : single_tip.receiver.notification_fields,
                'notification_selected' : single_tip.receiver.notification_selected,
                'tip_gus' : single_tip.tip_gus,
                'creation_time' : single_tip.internaltip.creation_date
            })

        store.close()

        return retVal

    @transact
    def get_receiver_by_tip(self, tip_gus):
        """
        @param tip_gus: a valid tip gus
        @return: Receiver description based on the associated tip_gus
        """
        store = self.getStore('get_receiver_by_tip')

        try:
            requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        except NotOneError, e:
            store.close()
            raise TipGusNotFoundError
        if not requested_t:
            store.close()
            raise TipGusNotFoundError

        retDict = requested_t.receiver._description_dict()
        store.close()
        return retDict


    # XXX this would be moved in the new 'task queue'
    @transact
    def flip_mark(self, tip_gus, newmark):

        notification_markers = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]

        if not newmark in notification_markers:
            raise Exception("Invalid developer brain dictionary", newmark)

        store = self.getStore('flip mark')

        requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        requested_t.notification_mark = newmark

        store.commit()
        store.close()

    @transact
    def admin_get_all(self):
        """
        this is called only by /admin/overview API
        """

        store = self.getStore('receivertip - admin_get_all')

        all_rt = store.find(ReceiverTip)

        retVal = []
        for single_rt in all_rt:
            retVal.append(single_rt._description_dict())

        store.close()
        return retVal

    @transact
    def admin_get_single(self, tip_gus):
        log.debug("[D] %s %s " % (__file__, __name__), "Class ReceiverTip", "admin_get_single", tip_gus)

        store = self.getStore('admin_get_single')

        try:
            requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        except NotOneError, e:
            store.close()
            raise TipGusNotFoundError
        if not requested_t:
            store.close()
            raise TipGusNotFoundError

        retDict = requested_t._description_dict()
        store.close()

        return retDict

    @transact
    def receiver_get_single(self, tip_gus):
        """
        This is the method called when a receiver is accessing to Tip. sometimes, the
        Receiver is listening: http://www.youtube.com/watch?v=MokNvbiRqCM but this do not
        interact with globaleaks, so, keep sharing! ;)
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class ReceiverTip", "receiver_get_single", tip_gus)

        store = self.getStore('receiver_get_single')

        try:
            requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        except NotOneError, e:
            store.close()
            raise TipGusNotFoundError
        if not requested_t:
            store.close()
            raise TipGusNotFoundError

        requested_t.last_activity = gltime.utcPrettyDateNow()
        store.commit()

        tip_details = requested_t.internaltip._description_dict()
        tip_details.pop('id')

        receivers_info = requested_t.internaltip._receivers_description()
        tip_info = requested_t._description_dict()

        ret_dict = { 'tip_details' : tip_details, 'tip_info' : tip_info, 'receivers_info' : receivers_info }

        store.close()

        return ret_dict

    @transact
    def receiver_get_index(self, tip_gus):
        """
        Return a small portion of the Tip, just the element useful to create tipIndexDict
        """

    @transact
    def pertinence_vote(self, tip_gus, vote):
        """
        check if the receiver has already voted. if YES: raise an exception, if NOT
        mark the expressed vote and call the internaltip to register the fact.
        @vote would be True or False, default is "I'm not expressed"
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class ReceiverTip", "pertinence_vote", tip_gus)

        store = self.getStore('pertinence_vote')

        try:
            requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        except NotOneError, e:
            store.close()
            raise TipGusNotFoundError
        if not requested_t:
            store.close()
            raise TipGusNotFoundError

        if requested_t.expressed_pertinence:
            store.close()
            raise TipPertinenceExpressed

        # expressed_pertinence has those meanings:
        # 0 = unassigned
        # 1 = negative vote
        # 2 = positive vote
        requested_t.expressed_pertinence = 2 if vote else 1

        requested_t.internaltip.pertinence_update(vote)
        requested_t.last_activity = gltime.utcPrettyDateNow()

        store.commit()
        store.close()

    @transact
    def total_delete(self, tip_gus):
        """
        checks if Receiver has the right of this operation, and forward to InternalTip.tip_total_delete()
        """
        pass

    @transact
    def personal_delete(self, tip_gus):
        """
        remove the Receiver Tip access, then forward to InternalTip.receiver_remove()
        """

        pass

    # This method is separated by initialize routine, because the tip creation
    # event can be exported/overriden/implemented by a plugin in a certain future.
    # like notification or delivery, it has a dedicated event in the scheduler
    @transact
    def create_receiver_tips(self, id, tier):
        """
        act on self. create the ReceiverTip based on self.receivers_map
        """
        log.debug("[D] %s %s " % (__file__, __name__), "ReceiverTip create_receiver_tips", id, "on tier", tier)

        store = self.getStore('create_receiver_tips')

        selected_it = store.find(InternalTip, InternalTip.id == id).one()

        for i, mapped in enumerate(selected_it.receivers_map):

            if not mapped['receiver_level'] == tier:
                continue

            receiver_subject = store.find(Receiver, Receiver.receiver_gus == selected_it.receivers_map[i]['receiver_gus']).one()

            receiver_tip =  ReceiverTip()

            # is initialized a Tip that need to be notified
            receiver_tip.initialize(mapped, selected_it, receiver_subject)

            receiver_subject.update_timings()

            selected_it.receivers_map[i]['tip_gus'] = receiver_tip.tip_gus
            store.add(receiver_tip)

        # commit InternalTip.receivers_map[only requested tier]['tip_gus'] & ReceiverTip(s)
        store.commit()
        store.close()

    # called by a transact operation, dump the ReceiverTip
    def _description_dict(self):

        descriptionDict = {
            'internaltip_id' : self.internaltip_id,
            'tip_gus' : self.tip_gus,
            'notification_mark' : self.notification_mark,
            'notification_date' : gltime.prettyDateTime(self.notification_date),
            'last_access' : gltime.prettyDateTime(self.last_access),
            'access_counter' : self.access_counter,
            'expressed_pertinence': self.expressed_pertinence,
            'receiver_gus' : self.receiver_gus,
            'receiver_name' : self.receiver.name,
            'authoptions' : self.authoptions
        }
        return descriptionDict


class WhistleblowerTip(TXModel):
    """
    WhisteleblowerTip is intended, at the moment, to provide a whistleblower access to the Tip.
    differently from the ReceiverTips, has a secret and/or authentication checks, has
    different capabilities, like: cannot not download, cannot express pertinence, and
    other operation permitted to the WB shall be configured by the Admin.
    """
    __storm_table__ = 'whistleblowertips'

    receipt = Unicode(primary=True)
        # receipt can be proposed by whistleblower, the globaleaks node *always* perform a
        # little modification on that (because NEED to be unique), before returining 
        # back. having a tip_gus was no more useful in whistleblower tip, has start to 
        # sound as a limit.

    authoptions = Pickle()
        # this would be choosen by the WB when submission is finalized, in example,
        # WB should decide to comeback only using the same client (= the same private key)
        # and a signature schema can be used. other options would be available,
        # they are not yet specified.

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)


    @transact
    def whistleblower_get_single(self, receipt):

        store = self.getStore('wb_tips - whistleblower_get_single ')

        try:
            requested_t = store.find(WhistleblowerTip, WhistleblowerTip.receipt == receipt).one()
        except NotOneError, e:
            store.close()
            raise TipReceiptNotFoundError
        if not requested_t:
            store.close()
            raise TipReceiptNotFoundError

        wb_tip_dict = requested_t.internaltip._description_dict()
        wb_tip_dict.pop('id')

        comments = requested_t.internaltip.get_comment_public()

        complete_tip_dict = wb_tip_dict
        complete_tip_dict.update({'receivers' : requested_t.internaltip._receivers_description() })
        complete_tip_dict.update({'comments' : comments})

        store.close()
        return complete_tip_dict

    @transact
    def admin_get_all(self):
        """
        This is called by API /admin/overview only
        """

        store = self.getStore('wb_tips - admin_get_all')

        all_wt = store.find(WhistleblowerTip)

        retVal = []
        for single_wt in all_wt:
            retVal.append(single_wt._description_dict())

        store.close()
        return retVal

    @transact
    def admin_get_single(self, receipt):
        log.debug("[D] %s %s " % (__file__, __name__), "Class WhistleBlowerTip", "admin_get_single", receipt)

        store = self.getStore('admin_get_single')

        try:
            requested_t = store.find(WhistleblowerTip, WhistleblowerTip.receipt == receipt).one()
        except NotOneError, e:
            store.close()
            log.err("[E] -- Collision fatal error, receipt is not unique [%s]" % receipt)
            raise TipGusNotFoundError
        if not requested_t:
            store.close()
            raise TipGusNotFoundError

        retDict = requested_t._description_dict()
        store.close()

        return retDict

    # called by a transact operation, dump the WhistleBlower Tip
    def _description_dict(self):

        descriptionDict = {
            'internaltip_id' : self.internaltip_id,
            'authoption' : self.authoptions,
            'receipt' : self.receipt
        }
        return descriptionDict

    @transact
    def delete_access(self):
        """
        a WhistleBlower can delete is own access.
        """
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
    shared = Bool()
    # track if this folder is shared or single

    property_applied = Pickle()
    # actually there are not property, but here would be marked if symmetric
    # asymmetric encryption has been used.

    upload_time = Date()

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)


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

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)


class Comment(TXModel):
    """
    This table handle the, 311 americano, remind.
    This table handle the comment collection, has an InternalTip referenced
    """
    __storm_table__ = 'comments'

    id = Int(primary=True)

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)

    creation_time = DateTime()
    source = Unicode()
    content = Unicode()
    author = Unicode()
    notification_mark = Unicode()


    @transact
    def add_comment(self, itip_id, comment, source, name=None):
        """
        @param itip_id: InternalTip.id of reference, need to be addressed
        @param comment: the unicode text expected to be recorded
        @param source: the source kind of the comment (receiver, wb, system)
        @param name: the Comment author name to be show and recorded, can be absent if source is enough
        @return: None
        """
        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip class", "add_comment",
            "itip_id", itip_id, "source", source, "name", name)

        if not source in [ u'receiver', u'whistleblower', u'system' ]:
            raise Exception("Invalid developer brain status", source)

        store = self.getStore('add_comment')

        # this approach is a little different from the other classes in ExternalTip
        # they use a new Object() in the caller method, and then Object.initialize
        # to fill with data.
        # XXX this would be refactored when TaskQueue would be engineered
        newcomment = Comment()
        newcomment.creation_time = gltime.utcTimeNow()
        newcomment.source = source
        newcomment.content = comment
        newcomment.author = name
        newcomment.notification_mark = u'not notified'
        newcomment.internaltip_id = itip_id
        store.add(newcomment)

        store.commit()
        store.close()


    # this is obvious, after the alpha release, all the mark/status info for the scheduler would be moved in
    # a dedicated class
    @transact
    def flip_mark(self, comment_id, newmark):

        log.debug("[D] %s %s " % (__file__, __name__), "Comment class", "flip_mark ", comment_id, newmark)

        notification_markers = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]

        if not newmark in notification_markers:
            raise Exception("Invalid developer brain dictionary", newmark)

        store = self.getStore('flip mark')

        requested_c = store.find(Comment, Comment.id  == comment_id).one()
        requested_c.notification_mark = newmark

        store.commit()
        store.close()


    @transact
    def get_comment_related(self, internltip_id):
        """
        return all the comment child of the same InternalTip.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Comment class", "get_comment_related", internltip_id)

        store = self.getStore('get_comment_related')

        comment_list = store.find(Comment, Comment.internaltip_id == internltip_id)

        retDict = []
        for single_comment in comment_list:
            retDict.append(single_comment._description_dict())

        store.close()
        return retDict

    @transact
    # XXX part of the schedule object refactor in TODO
    def get_comment_by_mark(self, marker):

        store = self.getStore('get_comment_by_mark')

        notification_markers = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]
        if not marker in notification_markers:
            raise Exception("Invalid developer brain dictionary", marker)

        marked_comments = store.find(Comment, Comment.notification_mark == marker)

        retVal = []
        for single_comment in marked_comments:
            retVal.append(single_comment._description_dict())

        store.close()
        return retVal

    @transact
    def admin_get_all(self):
        """
        This is called by API /admin/overview only
        """
        store = self.getStore('comment - admin_get_all')

        comments = store.find(Comment)

        retVal = []
        for single_c in comments:
            retVal.append(single_c._description_dict())

        store.close()
        return retVal

    def _description_dict(self):

        descriptionDict = {
            'comment_id' : self.id,
            'source' : self.source,
            'content' : self.content,
            'author' : self.author,
            'notification_mark': self.notification_mark,
            'internaltip_id' : self.internaltip_id,
            'creation_time' : gltime.prettyDateTime(self.creation_time)
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

    id = Int(primary=True)

    active_submissions = Int()
    node_activities = Int()
    uptime = Int()
