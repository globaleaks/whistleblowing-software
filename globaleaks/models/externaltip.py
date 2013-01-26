# -*- coding: UTF-8
#
#   models/externaltip
#   ******************
#
# implementation of Storm DB side of ReceiverTip and WhistleblowerTip
# and File and Comment tables, all those tables has relationship with
# InternalTip

from storm.twisted.transact import transact
from storm.exceptions import NotOneError
from storm.locals import Int, Pickle, Unicode, RawStr, Bool, DateTime, Reference
from storm.store import AutoReload

from globaleaks.utils import idops, log, gltime
from globaleaks.models.base import TXModel
from globaleaks.models.receiver import Receiver
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.context import Context
from globaleaks.rest.errors import TipGusNotFound, TipReceiptNotFound,\
    TipPertinenceExpressed, FileGusNotFound, InvalidInputFormat

__all__ = [ 'Folder', 'File', 'Comment', 'ReceiverTip', 'PublicStats', 'WhistleblowerTip' ]

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

    receiver_gus = Unicode()
    receiver = Reference(receiver_gus, Receiver.receiver_gus)

    notification_date = DateTime()
    notification_mark = Unicode()

    _marker = [ u'not notified', u'notified', u'unable to notify', u'notification ignore' ]

    @transact
    def new(self, itip_dict, receiver_dict):

        store = self.getStore()

        try:
            self.receiver_gus = unicode(receiver_dict['receiver_gus'])
            self.receiver = store.find(Receiver, Receiver.receiver_gus == unicode(self.receiver_gus) ).one()

            self.internaltip_id = int(itip_dict['internaltip_id'])
            self.internaltip = store.find(InternalTip, InternalTip.id == int(self.internaltip_id)).one()

            self.last_access = None
            self.access_counter = 0
            self.expressed_pertinence = 0

            self.notification_mark = self._marker[0] # 'not notified'
            self.notification_date = None
            self.tip_gus = idops.random_tip_gus()

        except KeyError, e:
            # The world will badly end, if this happen in non-tes
            raise InvalidInputFormat("Invalid messaged in Receiver Tip creation: bad key %s" % e)
        except TypeError, e:
            # The world will badly end, if this happen in non-tes
            raise InvalidInputFormat("Invalid messaged in Receiver Tip creation: bad type %s" % e)

        # XXX App log
        store.add(self)
        return self._description_dict()

    # -------------------
    # ReceiverTip has not:
    # update
    # _import_dict
    # -------------------

    @transact
    def update_notification_date(self, tip_gus):

        store = self.getStore()

        requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        requested_t.notification_date = gltime.utcTimeNow()

        return requested_t._description_dict()

    @transact
    def flip_mark(self, tip_gus, newmark):

        notification_markers = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]

        if not newmark in notification_markers:
            raise NotImplemented

        store = self.getStore()

        requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        requested_t.notification_mark = newmark

    @transact
    def get_all(self):
        """
        this is called only by /admin/overview API
        """
        store = self.getStore()

        all_rt = store.find(ReceiverTip)

        retVal = []
        for single_rt in all_rt:
            retVal.append(single_rt._description_dict())

        return retVal

    @transact
    def get_single(self, tip_gus):
        """
        This is the method called when a receiver is accessing to Tip. It return
        InternalTip details and update the last_access date.
        """
        store = self.getStore()

        try:
            requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        except NotOneError:
            raise TipGusNotFound
        if not requested_t:
            raise TipGusNotFound

        # Access counter is incremented before the data extraction,
        # last_access is incremented after (because the receiver want know
        # if someone has accesses in his place)
        requested_t.access_counter += 1

        # The single tip dump is composed by InternalTip + ReceiverTip details
        tip_details = requested_t.internaltip._description_dict()
        tip_details.update(requested_t._description_dict())

        requested_t.last_access = gltime.utcTimeNow()

        # every time the name 'id' is misused, a kitten die :(
        tip_details.update({ 'id' : requested_t.tip_gus })
        # XXX verifiy why need to be echoed back

        return dict(tip_details)


    @transact
    def pertinence_vote(self, tip_gus, vote):
        """
        check if the receiver has already voted. if YES: raise an exception, if NOT
        mark the expressed vote and call the internaltip to register the fact.
        @vote would be True or False, default is "I'm not expressed".

        return the actual vote expressed by all the receivers, to the same iTip.
        """

        store = self.getStore()

        try:
            requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        except NotOneError:
            raise TipGusNotFound
        if not requested_t:
            raise TipGusNotFound

        if requested_t.expressed_pertinence:
            raise TipPertinenceExpressed

        # expressed_pertinence has these meanings:
        # 0 = unassigned
        # 1 = negative vote
        # 2 = positive vote
        requested_t.expressed_pertinence = 2 if vote else 1
        requested_t.last_access = gltime.utcTimeNow()

        expressed_t = store.find(ReceiverTip, (ReceiverTip.internaltip_id == requested_t.internaltip_id, ReceiverTip.expressed_pertinence != 0))

        vote_sum = 0
        for et in expressed_t:
            if et.expressed_pertinence == 1:
                vote_sum -= 1
            else:
                vote_sum += 1

        itip_id_copy = requested_t.internaltip_id
        return (itip_id_copy, vote_sum)


    @transact
    def get_sibiligs_by_tip(self, tip_gus):
        """
        @param tip_gus: a valid tip_gus
        @return: a dict composed with:
            {
                'sibilings': [ sibilings_ReceiverTip ],
                'requested': this_ReceiverTip,
                'internaltip': InternalTip
            }
        this function is needed to perform "total delete" feature, return the
        list of all the ReceiverTip descending from the same InternalTip.

        This method is called by internal routine, not by Receiver
        """
        store = self.getStore()

        try:
            requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == unicode(tip_gus)).one()
        except NotOneError:
            raise TipGusNotFound
        if not requested_t:
            raise TipGusNotFound

        sibilings = store.find(ReceiverTip, ReceiverTip.internaltip_id == requested_t.internaltip_id)

        sibilings_description = []
        for s in sibilings:

            if s.tip_gus == requested_t.tip_gus:
                continue

            single_description = s._description_dict()
            sibilings_description.append(single_description)

        requested_description = requested_t._description_dict()
        internal_description = requested_t.internaltip._description_dict()

        retDict = {
                'sibilings': sibilings_description,
                'requested': requested_description,
                'internaltip' : internal_description
                }
        return retDict


    @transact
    def get_receivers_by_tip(self, tip_gus):
        """
        @param tip_gus: a valid tip gus
        @return: a list composed with:
            {
                'others' : [ other_Receivers ],
                'actor': this_Receiver,
                'mapped' [ mapped_receivers_in_itip]
            }
        The 'mapped' value can be ignored.

        The structured contain a complete receivers description, all the Receiver
        description working on the same InternalTip.
        """
        store = self.getStore()

        try:
            requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == unicode(tip_gus)).one()
        except NotOneError:
            raise TipGusNotFound
        if not requested_t:
            raise TipGusNotFound

        sibilings_tips = store.find(ReceiverTip, ReceiverTip.internaltip_id == requested_t.internaltip_id)

        other_receivers = []
        for s in sibilings_tips:

            if s.tip_gus == requested_t.tip_gus:
                continue

            receiver_desc = s.receiver._description_dict()
            other_receivers.append(receiver_desc)

        requester_receiver = requested_t.receiver._description_dict()
        internaltip_receivers =  list(requested_t.internaltip.receivers)

        retDict = { 'others': other_receivers,
                    'actor' : requester_receiver,
                    'mapped' : internaltip_receivers
                  }
        return retDict


    @transact
    def get_tips_by_tip(self, tip_gus):
        """
        @param tip_gus: a valid tip gus
        @return: a dict composed by:
            {
            'othertips': other_Tips_of_the_same_Receiver
            'request' : requested RecveiverTip
            }
        containing a complete ReceiverTip description.
        """
        store = self.getStore()

        try:
            requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == unicode(tip_gus)).one()
        except NotOneError:
            raise TipGusNotFound
        if not requested_t:
            raise TipGusNotFound

        other_tips = store.find(ReceiverTip, ReceiverTip.receiver_gus == requested_t.receiver_gus)

        tips = []
        for t in other_tips:

            if t.tip_gus == tip_gus:
                continue

            tips.append(t._description_dict())

        requested_tip = requested_t._description_dict()

        retDict = { 'othertips' : tips, 'request' : requested_tip }
        return retDict


    @transact
    def get_tips_by_receiver(self, receiver_gus):
        """
        @param receiver_gus: A receiver_gus
        @return: a list of ReceiverTip dict associated with receiver_gus
        """

        store = self.getStore()

        related_t = store.find(ReceiverTip, ReceiverTip.receiver_gus == unicode(receiver_gus))

        related_list = []
        for t in related_t:
            related_list.append(t._description_dict())

        return related_list


    @transact
    def get_tips_by_notification_mark(self, marker):
        """
        @param marker: one valid marker
        @return: a list of [ ReceiverTip ]
        """
        notification_markers = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]
        store = self.getStore()

        if unicode(marker) not in notification_markers:
            raise NotImplemented

        marked_t = store.find(ReceiverTip, ReceiverTip.notification_mark == unicode(marker))

        list_by_mark = []
        for t in marked_t:
            common_rtip_desc = t._description_dict()
            common_rtip_desc.update({'context_gus':t.internaltip.context_gus})
            list_by_mark.append(common_rtip_desc)
            # every dict returned from this method, explicit the context, instead get them from itip

        return list_by_mark


    @transact
    def get_tips_by_context(self, context_gus):
        """
        This function works as observer of all the Tips related to a specific Context,
        This method need to stay in externaltip.py, but for the Storm dependencies
        I've to choose just one Class in which put this function.

        @param context_gus:
        @return: a dict with the keys:
            'internaltip' : InternalTip,
            'receivertip' : [ ReceiverTips]
            'whistleblowertip' : [ WhistleBlowerTip ]
            'comments' : [ Comment ]
            'files' : [ Files ]

        Remind: this operation can be avoided if DELETE ON CASCADE would be
        stable and packed into Storm, but I've see works in this topic half month ago,
        now is the 28 Dec 2012, AKA Year 0 month 0 day 7 AMF (after the MayaFailure )
        """

        retList = []

        store = self.getStore()
        itip_related = store.find(InternalTip, InternalTip.context_gus == unicode(context_gus))

        for itip in itip_related:

            receiverD = []
            wbtD = []
            fileD = []
            commentD = []

            itipD = itip._description_dict()

            rtips = store.find(ReceiverTip, ReceiverTip.internaltip_id == itip.id )
            for r in rtips:
                receiverD.append(r._description_dict())

            wtips = store.find(WhistleblowerTip, WhistleblowerTip.internaltip_id == itip.id )
            for w in wtips:
                wbtD.append(w._description_dict())

            comments = store.find(Comment, Comment.internaltip_id == itip.id )
            for c in comments:
                commentD.append(c._description_dict())

            files = store.find(File, File.internaltip_id == itip.id )
            for f in files:
                fileD.append(f._description_dict())

            internaltip_related =  {
                "internaltip" : itipD,
                "receivertip" : receiverD,
                "whistleblowertip" : wbtD,
                "comments" : commentD,
                "files" : fileD
            }

            # TODO Applicative log
            print "Cascade remove of: itip", itipD['internaltip_id'],\
                "rtip", len(receiverD), "comments", len(commentD), "files", len(fileD)
            retList.append(internaltip_related)

        return retList

    @transact
    def personal_delete(self, tip_gus):
        """
        remove the Receiver Tip access.
        Happen when a Receiver choose to remove himself from a single Tip analysis,
            more massive form of Tip remove, are handled by the 'massive_delete' below
        Is called by handler, handler checks and align eventually references
        """

        store = self.getStore()

        try:
            requested_t = store.find(ReceiverTip, ReceiverTip.tip_gus == unicode(tip_gus)).one()
        except NotOneError:
            raise TipGusNotFound
        if not requested_t:
            raise TipGusNotFound

        store.remove(requested_t)

    @transact
    def massive_delete(self, internaltip_id):
        """
        remove the Receiver Tip access.
        Happen when a when a Context is deleted
            when an InternalTip is deleted
            when an InternalTip is expired
        Is called by handler, handler checks and align eventually references
        """

        store = self.getStore()
        # Sadly the matching query can't be used in store.remove()
        related_tips = store.find(ReceiverTip, ReceiverTip.internaltip_id == int(internaltip_id))
        for single_tip in related_tips:
            store.remove(single_tip)


    # called by a transact operation,dump the ReceiverTip (without the Tip details,
    # they stay in InternalTip)
    def _description_dict(self):

        descriptionDict = {
            'internaltip_id' : unicode(self.internaltip_id),
            'tip_gus' : unicode(self.tip_gus),
            'notification_mark' : bool(self.notification_mark),
            'notification_date' : unicode(gltime.prettyDateTime(self.notification_date)),
            'last_access' : unicode(gltime.prettyDateTime(self.last_access)) if self.last_access else u'Never',
            'access_counter' : unicode(self.access_counter),
            'expressed_pertinence': unicode(self.expressed_pertinence),
            'receiver_gus' : unicode(self.receiver_gus),
            'receiver_name' : unicode(self.receiver.name),
        }
        return dict(descriptionDict)


class WhistleblowerTip(TXModel):
    """
    WhisteleblowerTip is intended, to provide a whistleblower access to the Tip.
    Has ome differencies from the ReceiverTips: has a secret authentication checks, has
    different capabilities, like: cannot not download, cannot express pertinence.
    """

    __storm_table__ = 'whistleblowertips'

    receipt = Unicode(primary=True)

    last_access = DateTime()
    access_counter = Int()

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)

    @transact
    def new(self, internaltip_desc):

        store = self.getStore()

        try:
            self.internaltip_id = int(internaltip_desc['internaltip_id'])
        except TypeError:
            raise InvalidInputFormat("Unable to initialized WhistleBlower Tip with iTip (wrong field)")
        except KeyError:
            raise InvalidInputFormat("Unable to initialized WhistleBlower Tip with iTip (missing field)")

        self.internaltip = store.find(InternalTip, InternalTip.id == int(self.internaltip_id)).one()

        self.last_access = 0
        self.access_counter = 0

        self.receipt = unicode(idops.random_receipt())

        store.add(self)

        return self._description_dict()

    # Also this Model has not an update interface.

    @transact
    def get_single(self, receipt):

        store = self.getStore()

        try:
            requested_t = store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()
        except NotOneError:
            raise TipReceiptNotFound
        if not requested_t:
            raise TipReceiptNotFound

        requested_t.access_counter += 1

        # The single tip dump is composed by InternalTip + WBTip details
        tip_details = requested_t.internaltip._description_dict()
        tip_details.update(requested_t._description_dict())

        requested_t.last_access = gltime.utcTimeNow()

        # every time the name 'id' is misused, a kitten die :(
        tip_details.update({ 'id' : requested_t.receipt })
        # XXX verifiy why need to be echoed back

        return dict(tip_details)


    @transact
    def get_all(self):
        """
        This is called by API /admin/overview only
        """
        store = self.getStore()

        all_wt = store.find(WhistleblowerTip)

        retVal = []
        for single_wt in all_wt:
            retVal.append(single_wt._description_dict())

        return retVal


    @transact
    def delete_access(self, receipt):
        """
        a WhistleBlower can delete is own access, removing Whistleblower tip and invalidating the receipt
        """
        # XXX Log + system comment need to be called by handler, not by model
        store = self.getStore()

        try:
            requested_t = store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()
        except NotOneError:
            raise TipReceiptNotFound
        if not requested_t:
            raise TipReceiptNotFound

        store.remove(requested_t)

    @transact
    def delete_access_by_itip(self, internaltip_id):
        """
        Called by cascade delete from DELETE admin/context, or by Tip (total_delete)
        """
        store = self.getStore()

        try:
            selected = store.find(WhistleblowerTip, WhistleblowerTip.internaltip_id == int(internaltip_id))
        except NotOneError:
            raise Exception("internaltip_id do not exists: %d", internaltip_id)
        if not selected:
            raise Exception("internaltip_id do not exists: %d", internaltip_id)

        for single_tip in selected:
            store.remove(single_tip)


    # called by a transact operation, dump the WhistleBlower Tip
    def _description_dict(self):

        descriptionDict = {
            'last_access' :  unicode(gltime.prettyDateTime(self.last_access)) if not self.last_access else u'Never',
            'access_counter' : int(self.access_counter),
            'internaltip_id' : int(self.internaltip_id),
            'receipt' : unicode(self.receipt)
        }
        return dict(descriptionDict)


class File(TXModel):
    """
    The file are *stored* here, along with their properties
    """
    __storm_table__ = 'files'

    file_gus = Unicode(primary=True)

    name = Unicode()

    content = RawStr()
    shasum = RawStr() # XXX ?

    completed = Bool() # XXX remove ?

    description = Unicode()
    content_type = Unicode()
    mark = Unicode()

    size = Int()

    metadata_cleaned = Bool()
    uploaded_date = DateTime()

    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)

    # ----------------------------------------
    # Remind, only one of those reference is indexed in a time.
    #
    # If Submission: the file need to be processed
    # If InternalTip: the file need to be stored or served
    # If ReceiverTIp: the file is personally encrypted or different for every receiver
    #
    receivertip_gus = Unicode()
    internaltip_id = Int()
    submission_gus = Unicode()
    #
    # TODO make special validator supporting the "None" value
    # ----------------------------------------

    _marker = [ u'not processed', u'ready', u'blocked', u'stored' ]

    @transact
    def new(self, received_dict):

        store = self.getStore()

        try:
            self._import_dict(received_dict)

            # these three fields are accepted only in new()
            self.content_type = unicode(received_dict['content_type'])
            self.size = int(received_dict['file_size'])
            self.context_gus = unicode(received_dict['context_gus'])
            self.submission_gus = unicode(received_dict['submission_gus'])

        except KeyError, e:
            raise InvalidInputFormat("File import failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("File import failed (wrong %s)" % e)

        try:
            self.context = store.find(Context, Context.context_gus == self.context_gus).one()

        except NotOneError:
            # This can never happen
            raise Exception("Internal Impossible Error")

        self.mark = self._marker[0] # not processed
        self.completed = False
        self.uploaded_date = gltime.utcTimeNow()

        self.file_gus = unicode(idops.random_file_gus())

        # When the file is 'not processed', this value stay to 0
        self.internaltip_id = 0

        store.add(self)
        return self._description_dict()


    # update in short modify only filename and description, at the moment API is missing
    # Remind open ticket with GLClient
    @transact
    def update(self, file_gus, received_dict):

        store = self.getStore()

        try:
            referenced_f = store.find(File, File.file_gus == unicode(file_gus)).one()
        except NotOneError:
            raise FileGusNotFound
        if not referenced_f:
            raise FileGusNotFound

        try:
            referenced_f._import_dict(received_dict)
        except KeyError, e:
            raise InvalidInputFormat("File update failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("File update failed (wrong %s)" % e)

        return referenced_f._description_dict()


    @transact
    def _import_dict(self, received_dict):

        self.name = unicode(received_dict['filename'])
        self.description = unicode(received_dict['description'])

    @transact
    def flip_mark(self, file_gus, newmark):

        if not newmark in self._marker:
            raise NotImplemented

        store = self.getStore()

        requested_f = store.find(File, File.file_gus == unicode(file_gus)).one()

        if not requested_f:
            raise FileGusNotFound

        requested_f.mark = newmark

    @transact
    def get_file_by_marker(self, marker):
        """
        @return: all the files matching with the requested
            marked, between this list of option:
        marker_avail = [ u'not processed', u'ready', u'blocked'  ]

        'delivered' and 'stored' depends from the single Receiver
        TODO handle that with the schedule queue
        """

        store = self.getStore()

        if not marker in self._marker:
            Exception("Implementation error")

        req_fi = store.find(File, File.mark == marker)

        retVal = []
        for single_file in req_fi:
            retVal.append(single_file._description_dict())

        return retVal


    @transact
    def get_files_by_itip(self, internaltip_id):

        store = self.getStore()

        referenced_f = store.find(File, File.internaltip_id == int(internaltip_id))

        referenced_files = []

        for single_file in referenced_f:
            referenced_files.append(single_file._description_dict())

        return referenced_files


    @transact
    def delete_file_by_itip(self, internaltip_id):

        store = self.getStore()

        referenced_f = store.find(File, File.internaltip_id == int(internaltip_id))

        counter_test = 0
        for single_f in referenced_f:
            counter_test += 1
            store.remove(single_f)

        return counter_test


    @transact
    def get_all(self):

        store = self.getStore()
        files = store.find(File)

        all_files = []
        for single_file in files:
            all_files.append(single_file._description_dict())

        return all_files

    @transact
    def get_all_by_submission(self, submission_gus):

        store = self.getStore()
        selected_f = store.find(File, File.submission_gus == unicode(submission_gus))

        submission_files = []
        for single_file in selected_f:
            submission_files.append(single_file._description_dict())

        return submission_files


    @transact
    def get_single(self, file_gus):

        store = self.getStore()

        try:
            filelookedat = store.find(File, File.file_gus == unicode(file_gus)).one()
        except NotOneError:
            raise FileGusNotFound
        if not filelookedat:
            raise FileGusNotFound

        return filelookedat._description_dict()

    def _description_dict(self):

        # Note: the content is not serialized
        descriptionDict = {
            'size' : self.size,
            'file_gus' : self.file_gus,
            'content_type' : self.content_type,
            'file_name' : self.name,
            'description' : self.description,
            'uploaded_date': gltime.prettyDateTime(self.uploaded_date),
            'completed' : self.completed,
            'metadata_cleaned' : self.metadata_cleaned,
            'context_gus' : self.context_gus,
            'submission_gus' :  self.submission_gus if self.submission_gus else False,
            'internaltip_id' : self.internaltip_id if self.internaltip_id else False,
            'receivertip_gus' :  self.receivertip_gus if self.receivertip_gus else False

        }
        return dict(descriptionDict)


class Comment(TXModel):
    """
    This table handle the, 311 americano, remind.
    This table handle the comment collection, has an InternalTip referenced
    """
    __storm_table__ = 'comments'

    id = Int(primary=True, default=AutoReload)

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)

    creation_time = DateTime()
    source = Unicode()
    content = Unicode()
    author_gus = Unicode()
    notification_mark = Unicode()

    @transact
    def add_comment(self, itip_id, comment, source, author_gus=None):
        """
        @param itip_id: InternalTip.id of reference, need to be addressed
        @param comment: the unicode text expected to be recorded
        @param source: the source kind of the comment (receiver, wb, system)
        @param name: the Comment wb_r name to be show and recorded, can be absent if source is enough
        @return: None
        """

        if not source in [ u'receiver', u'whistleblower', u'system' ]:
            raise NotImplemented

        store = self.getStore()

        try:
            itip = store.find(InternalTip, InternalTip.id == int(itip_id)).one()
        except NotOneError:
            # This can't actually happen
            raise Exception
        if itip is None:
            # This can't actually happen
            raise Exception

        # this approach is a little different from the other classes in ExternalTip
        # they use a new Object() in the caller method, and then Object.initialize
        # to fill with data.
        newcomment = Comment()

        newcomment.creation_time = gltime.utcTimeNow()
        newcomment.source = source
        newcomment.content = comment
        newcomment.author_gus = author_gus
        newcomment.internaltip = itip
        newcomment.internaltip_id = int(itip_id)

        # TODO |need to be reeingineered, only with the queue task
        # TODO |manager can be digest and track the single notification.
        # TODO |
        newcomment.notification_mark = u'not notified'
        store.add(newcomment)

        return newcomment._description_dict()


    @transact
    def flip_mark(self, comment_id, newmark):

        notification_markers = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]

        if not newmark in notification_markers:
            raise NotImplemented

        store = self.getStore()

        requested_c = store.find(Comment, Comment.id  == int(comment_id)).one()
        requested_c.notification_mark = newmark


    @transact
    def delete_comment_by_itip(self, internaltip_id):

        store = self.getStore()

        comments_selected = store.find(Comment, Comment.internaltip_id ==  int(internaltip_id))

        counter_test = 0
        for single_c in comments_selected:
            counter_test += 1
            store.remove(single_c)

        return counter_test

    @transact
    def get_comment_by_itip(self, internaltip_id):

        store = self.getStore()

        comments_selected = store.find(Comment, Comment.internaltip_id ==  int(internaltip_id))

        retList = []
        for single_c in comments_selected:
            retList.append(single_c._description_dict())

        return retList

    @transact
    def get_comment_by_mark(self, marker):

        store = self.getStore()

        notification_markers = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]
        if not marker in notification_markers:
            raise NotImplemented

        marked_comments = store.find(Comment, Comment.notification_mark == marker)

        retVal = []
        for single_comment in marked_comments:
            retVal.append(single_comment._description_dict())

        return retVal


    @transact
    def get_all(self):
        """
        This is called by API /admin/overview only
        """
        store = self.getStore()

        comments = store.find(Comment)

        retVal = []
        for single_c in comments:
            retVal.append(single_c._description_dict())

        return retVal

    def _description_dict(self):

        descriptionDict = {
            'comment_id' : unicode(self.id),
            'source' : unicode(self.source),
            'content' : unicode(self.content),
            'author_gus' : unicode(self.author_gus),
            'notification_mark': bool(self.notification_mark),
            'internaltip_id' : int(self.internaltip_id),
            'creation_time' : unicode(gltime.prettyDateTime(self.creation_time))
        }
        return dict(descriptionDict)




