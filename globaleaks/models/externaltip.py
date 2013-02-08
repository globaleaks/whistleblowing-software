# -*- coding: UTF-8
#
#   models/externaltip
#   ******************
#
# implementation of Storm DB side of ReceiverTip and WhistleblowerTip
# and File and Comment tables, all those tables has relationship with
# InternalTip

from storm.exceptions import NotOneError
from storm.locals import Int, Pickle, Unicode, RawStr, DateTime, Reference
from storm.store import AutoReload
from twisted.internet import fdesc

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


    def new(self, itip_dict, receiver_dict):

        try:
            self.tip_gus = idops.random_tip_gus()

            self.receiver_gus = unicode(receiver_dict['receiver_gus'])
            self.receiver = self.store.find(Receiver, Receiver.receiver_gus == unicode(self.receiver_gus) ).one()

            self.internaltip_id = int(itip_dict['internaltip_id'])
            self.internaltip = self.store.find(InternalTip, InternalTip.id == int(self.internaltip_id)).one()

            self.last_access = None
            self.access_counter = 0
            self.expressed_pertinence = 0

            self.notification_mark = self._marker[0] # 'not notified'
            self.notification_date = None

        except KeyError, e:
            raise InvalidInputFormat("Invalid messaged in Receiver Tip creation: bad key %s" % e)
        except TypeError, e:
            raise InvalidInputFormat("Invalid messaged in Receiver Tip creation: bad type %s" % e)

        # XXX App log
        self.store.add(self)
        return self._description_dict()

    # -------------------
    # ReceiverTip has not:
    # update
    # _import_dict
    # -------------------

    def update_notification_date(self, tip_gus):

        requested_t = self.store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        requested_t.notification_date = gltime.utcTimeNow()

        return requested_t._description_dict()


    def flip_mark(self, tip_gus, newmark):

        notification_markers = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]

        if not newmark in notification_markers:
            raise NotImplemented

        requested_t = self.store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
        requested_t.notification_mark = newmark


    def get_all(self):
        """
        this is called only by /admin/overview API
        """
        all_rt = self.store.find(ReceiverTip)

        retVal = []
        for single_rt in all_rt:
            retVal.append(single_rt._description_dict())

        return retVal


    def get_single(self, tip_gus):
        """
        This is the method called when a receiver is accessing to Tip. It return
        InternalTip details and update the last_access date.
        """
        try:
            requested_t = self.store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
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


    def pertinence_vote(self, tip_gus, vote):
        """
        check if the receiver has already voted. if YES: raise an exception, if NOT
        mark the expressed vote and call the internaltip to register the fact.
        @vote would be True or False, default is "I'm not expressed".

        return the actual vote expressed by all the receivers, to the same iTip.
        """

        try:
            requested_t = self.store.find(ReceiverTip, ReceiverTip.tip_gus == tip_gus).one()
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

        expressed_t = self.store.find(ReceiverTip, (ReceiverTip.internaltip_id == requested_t.internaltip_id, ReceiverTip.expressed_pertinence != 0))

        vote_sum = 0
        for et in expressed_t:
            if et.expressed_pertinence == 1:
                vote_sum -= 1
            else:
                vote_sum += 1

        itip_id_copy = requested_t.internaltip_id
        return (itip_id_copy, vote_sum)


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
        try:
            requested_t = self.store.find(ReceiverTip, ReceiverTip.tip_gus == unicode(tip_gus)).one()
        except NotOneError:
            raise TipGusNotFound
        if not requested_t:
            raise TipGusNotFound

        sibilings = self.store.find(ReceiverTip, ReceiverTip.internaltip_id == requested_t.internaltip_id)

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


    # maybe not more used, after the auth change. verify if is needed
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
        try:
            requested_t = self.store.find(ReceiverTip, ReceiverTip.tip_gus == unicode(tip_gus)).one()
        except NotOneError:
            raise TipGusNotFound
        if not requested_t:
            raise TipGusNotFound

        sibilings_tips = self.store.find(ReceiverTip, ReceiverTip.internaltip_id == requested_t.internaltip_id)

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


    def get_tips_by_itip(self, itip_id):

        requested_t = self.store.find(ReceiverTip, ReceiverTip.internaltip_id == int(itip_id))

        retList = []
        for tip in requested_t:
            retList.append(tip._description_dict())

        return retList


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
        try:
            requested_t = self.store.find(ReceiverTip, ReceiverTip.tip_gus == unicode(tip_gus)).one()
        except NotOneError:
            raise TipGusNotFound
        if not requested_t:
            raise TipGusNotFound

        other_tips = self.store.find(ReceiverTip, ReceiverTip.receiver_gus == requested_t.receiver_gus)

        tips = []
        for t in other_tips:

            if t.tip_gus == tip_gus:
                continue

            tips.append(t._description_dict())

        requested_tip = requested_t._description_dict()

        retDict = { 'othertips' : tips, 'request' : requested_tip }
        return retDict


    def get_tips_by_receiver(self, receiver_gus):
        """
        @param receiver_gus: A receiver_gus
        @return: a list of ReceiverTip dict associated with receiver_gus
        """

        related_t = self.store.find(ReceiverTip, ReceiverTip.receiver_gus == unicode(receiver_gus))

        related_list = []
        for t in related_t:
            related_list.append(t._description_dict())

        return related_list


    def get_tips_by_notification_mark(self, marker):
        """
        @param marker: one valid marker
        @return: a list of [ ReceiverTip ]
        """
        notification_markers = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]

        if unicode(marker) not in notification_markers:
            raise NotImplemented

        marked_t = self.store.find(ReceiverTip, ReceiverTip.notification_mark == unicode(marker))

        list_by_mark = []
        for t in marked_t:
            common_rtip_desc = t._description_dict()
            common_rtip_desc.update({'context_gus':t.internaltip.context_gus})
            list_by_mark.append(common_rtip_desc)
            # every dict returned from this method, explicit the context, instead get them from itip

        return list_by_mark


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

        itip_related = self.store.find(InternalTip, InternalTip.context_gus == unicode(context_gus))

        for itip in itip_related:

            receiverD = []
            wbtD = []
            fileD = []
            commentD = []

            itipD = itip._description_dict()

            rtips = self.store.find(ReceiverTip, ReceiverTip.internaltip_id == itip.id )
            for r in rtips:
                receiverD.append(r._description_dict())

            wtips = self.store.find(WhistleblowerTip, WhistleblowerTip.internaltip_id == itip.id )
            for w in wtips:
                wbtD.append(w._description_dict())

            comments = self.store.find(Comment, Comment.internaltip_id == itip.id )
            for c in comments:
                commentD.append(c._description_dict())

            files = self.store.find(File, File.internaltip_id == itip.id )
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


    def personal_delete(self, tip_gus):
        """
        remove the Receiver Tip access.
        Happen when a Receiver choose to remove himself from a single Tip analysis,
            more massive form of Tip remove, are handled by the 'massive_delete' below
        Is called by handler, handler checks and align eventually references
        """

        try:
            requested_t = self.store.find(ReceiverTip, ReceiverTip.tip_gus == unicode(tip_gus)).one()
        except NotOneError:
            raise TipGusNotFound
        if not requested_t:
            raise TipGusNotFound

        self.store.remove(requested_t)


    def massive_delete(self, internaltip_id):
        """
        remove the Receiver Tip access.
        Happen when a when a Context is deleted
            when an InternalTip is deleted
            when an InternalTip is expired
        Is called by handler, handler checks and align eventually references
        """

        # Sadly the matching query can't be used in self.store.remove()
        related_tips = self.store.find(ReceiverTip, ReceiverTip.internaltip_id == int(internaltip_id))
        for single_tip in related_tips:
            self.store.remove(single_tip)


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


    def new(self, internaltip_desc):

        try:
            self.internaltip_id = int(internaltip_desc['internaltip_id'])
        except TypeError:
            raise InvalidInputFormat("Unable to initialized WhistleBlower Tip with iTip (wrong field)")
        except KeyError:
            raise InvalidInputFormat("Unable to initialized WhistleBlower Tip with iTip (missing field)")

        self.receipt = unicode(idops.random_receipt())
        self.last_access = 0
        self.access_counter = 0

        self.internaltip = self.store.find(InternalTip, InternalTip.id == int(self.internaltip_id)).one()

        self.store.add(self)

        return self._description_dict()

    # Also this Model has not an update interface.

    def get_single(self, receipt):

        try:
            requested_t = self.store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()
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


    def get_all(self):
        """
        This is called by API /admin/overview only
        """

        all_wt = self.store.find(WhistleblowerTip)

        retVal = []
        for single_wt in all_wt:
            retVal.append(single_wt._description_dict())

        return retVal


    def delete_access(self, receipt):
        """
        a WhistleBlower can delete is own access, removing Whistleblower tip and invalidating the receipt
        """
        # XXX Log + system comment need to be called by handler, not by model

        try:
            requested_t = self.store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()
        except NotOneError:
            raise TipReceiptNotFound
        if not requested_t:
            raise TipReceiptNotFound

        self.store.remove(requested_t)


    def delete_access_by_itip(self, internaltip_id):
        """
        Called by cascade delete from DELETE admin/context, or by Tip (total_delete)
        """

        try:
            selected = self.store.find(WhistleblowerTip, WhistleblowerTip.internaltip_id == int(internaltip_id))
        except NotOneError:
            raise Exception("internaltip_id do not exists: %d", internaltip_id)
        if not selected:
            raise Exception("internaltip_id do not exists: %d", internaltip_id)

        for single_tip in selected:
            self.store.remove(single_tip)


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
    sha2sum = Unicode()

    description = Unicode()
    content_type = Unicode()
    mark = Unicode()
    size = Int()
    uploaded_date = DateTime()

    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)

    # ----------------------------------------
    # Remind, only one of those reference is indexed in a time.
    #
    submission_gus = Unicode()
    internaltip_id = Int()
    #
    # If Submission: the file need to be processed
    # If InternalTip: the file need to be stored or served

    _marker = [ u'not processed', u'ready', u'blocked', u'stored' ]

    def new(self, received_dict):

        try:
            self.file_gus = unicode(idops.random_file_gus())

            self._import_dict(received_dict)

            # these fields are accepted only in new()
            self.content_type = unicode(received_dict['content_type'])
            self.size = int(received_dict['file_size'])
            self.context_gus = unicode(received_dict['context_gus'])

            # catch a file uploaded in a Tip of in a Submission
            if received_dict['submission_gus']:
                self.submission_gus = unicode(received_dict['submission_gus'])
                self.internaltip_id = 0
            elif received_dict['internaltip_id']:
                self.internaltip_id = int(received_dict['internaltip_id'])
                self.submission_gus = None
            else:
                raise NotImplementedError("Missing Submission/InternalTip value")

        except KeyError, e:
            raise InvalidInputFormat("File import failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("File import failed (wrong %s)" % e)

        try:
            self.context = self.store.find(Context, Context.context_gus == self.context_gus).one()

        except NotOneError:
            # This can never happen
            raise Exception("Internal Impossible Error")

        self.uploaded_date = gltime.utcTimeNow()

        self.mark = self._marker[0] # not processed

        self.store.add(self)
        return self._description_dict()


    # update in short modify only filename and description, at the moment API is missing
    # Remind open ticket with GLClient

    def update(self, file_gus, received_dict):

        try:
            referenced_f = self.store.find(File, File.file_gus == unicode(file_gus)).one()
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


    def switch_reference(self, submission_dict, internaltip_dict):
        """
        @param submission_dict:
        @param internaltip_dict:

        When a submission became promoted as InternalTip, verify that all
        the files has been concluded (or mark them as broken), switch the
        ownsership from a submission_gus to an internaltip_id
        """

        sf = self.store.find(File, File.submission_gus == submission_dict['submission_gus'])

        for fil in sf:

            fil.submission_gus = None
            itid = internaltip_dict['internaltip_id']
            print "switch file %s reference from submission to Tip (%d byte) %d itid " % \
                  ( unicode(fil.name), int(fil.size), int(itid))
            fil.internaltip_id = int(itid)


    def _import_dict(self, received_dict):

        self.name = unicode(received_dict['filename'])
        self.description = unicode(received_dict['description'])

    def flip_mark(self, file_gus, newmark, sha2sum=None):

        if not newmark in self._marker:
            raise NotImplemented

        requested_f = self.store.find(File, File.file_gus == unicode(file_gus)).one()

        if not requested_f:
            raise FileGusNotFound

        print "Shifting file mark from %s to %s sha %s" % (requested_f.mark, newmark, sha2sum)
        requested_f.mark = newmark

        if sha2sum:
            requested_f.sha2sum = unicode(sha2sum)

    def add_content_from_fs(self, file_gus, filepath):

        requested_f = self.store.find(File, File.file_gus == unicode(file_gus)).one()

        chunk_size = 8192

        with open(filepath, 'rb') as fd:

            bytecount = 0
            requested_f.content = ''

            fdesc.setNonBlocking(fd.fileno())
            while True:
                chunk = fd.read(chunk_size)
                if len(chunk) == 0:
                    break
                bytecount += len(chunk)
                requested_f.content += chunk

        print "Moved content from", filepath, "to the database", file_gus, "byte", bytecount

    def get_file_by_marker(self, marker):
        """
        @return: all the files matching with the requested
            marked, between this list of option:
        marker_avail = [ u'not processed', u'ready', u'blocked'  ]

        'delivered' and 'stored' depends from the single Receiver
        TODO handle that with the schedule queue
        """

        if not marker in self._marker:
            Exception("Implementation error")

        req_fi = self.store.find(File, File.mark == marker)

        retVal = []
        for single_file in req_fi:
            retVal.append(single_file._description_dict())

        return retVal


    def get_files_by_itip(self, internaltip_id):

        referenced_f = self.store.find(File, File.internaltip_id == int(internaltip_id))

        referenced_files = []

        for single_file in referenced_f:
            referenced_files.append(single_file._description_dict())

        return referenced_files


    def delete_file_by_itip(self, internaltip_id):

        referenced_f = self.store.find(File, File.internaltip_id == int(internaltip_id))

        counter_test = 0
        for single_f in referenced_f:
            counter_test += 1
            self.store.remove(single_f)

        return counter_test


    def get_all(self):

        files = self.store.find(File)

        all_files = []
        for single_file in files:
            all_files.append(single_file._description_dict())

        return all_files


    def get_all_by_submission(self, submission_gus):

        selected_f = self.store.find(File, File.submission_gus == unicode(submission_gus))

        submission_files = []
        for single_file in selected_f:
            submission_files.append(single_file._description_dict())

        return submission_files

    def get_content(self, file_gus):

        print file_gus
        try:
            filelookedat = self.store.find(File, File.file_gus == unicode(file_gus)).one()
        except NotOneError:
            raise FileGusNotFound
        if not filelookedat:
            raise FileGusNotFound

        ret={ 'content' : filelookedat.content,
              'sha2sum' : filelookedat.sha2sum,
              'size' : filelookedat.size,
              'content_type' : filelookedat.content_type,
              'file_name' : filelookedat.name }
        return ret


    def get_single(self, file_gus):

        try:
            filelookedat = self.store.find(File, File.file_gus == unicode(file_gus)).one()
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
            'mark' : unicode(self.mark),
            'sha2sum' : unicode(self.sha2sum),
            'context_gus' : self.context_gus,
            'submission_gus' :  self.submission_gus if self.submission_gus else False,
            'internaltip_id' : self.internaltip_id if self.internaltip_id else False,

        }
        return dict(descriptionDict)


class Comment(TXModel):
    """
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

    _marker = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]

    def new(self, itip_id, comment, source, author_gus=None):
        """
        @param itip_id: InternalTip.id of reference, need to be addressed
        @param comment: the unicode text expected to be recorded
        @param source: the source kind of the comment (receiver, wb, system)
        @param name: the Comment wb_r name to be show and recorded, can be absent if source is enough
        @return: None
        """

        if not source in [ u'receiver', u'whistleblower', u'system' ]:
            raise NotImplemented

        try:
            itip = self.store.find(InternalTip, InternalTip.id == int(itip_id)).one()
        except NotOneError:
            # This can't actually happen
            raise Exception
        if itip is None:
            # This can't actually happen
            raise Exception

        # this approach is a little different from the other classes in ExternalTip
        # they use a new Object() in the caller method, and then Object.initialize
        # to fill with data.

        try:
            self.creation_time = gltime.utcTimeNow()
            self.source = source
            self.content = comment
            self.author_gus = author_gus
            self.internaltip = itip
            self.internaltip_id = int(itip_id)
        except TypeError, e:
            raise InvalidInputFormat("Unable to create comment: (wrong %s)" % e )

        # Remind, notification is not reliable until Task Queue do not born
        self.notification_mark = self._marker[0]
        self.store.add(self)

        return self._description_dict()

    # Comment has not _import_dict and update, because a comment can't be updated at the moment.

    def flip_mark(self, comment_id, newmark):

        if not newmark in self._marker:
            raise NotImplemented

        requested_c = self.store.find(Comment, Comment.id  == int(comment_id)).one()
        requested_c.notification_mark = newmark


    def delete_comment_by_itip(self, internaltip_id):

        comments_selected = self.store.find(Comment, Comment.internaltip_id ==  int(internaltip_id))

        counter_test = 0
        for single_c in comments_selected:
            counter_test += 1
            self.store.remove(single_c)

        return counter_test


    def get_comment_by_itip(self, internaltip_id):

        comments_selected = self.store.find(Comment, Comment.internaltip_id ==  int(internaltip_id))

        retList = []
        for single_c in comments_selected:
            retList.append(single_c._description_dict())

        return retList


    def get_comment_by_mark(self, marker):

        if not marker in self._marker:
            raise NotImplemented

        marked_comments = self.store.find(Comment, Comment.notification_mark == marker)

        retVal = []
        for single_comment in marked_comments:
            retVal.append(single_comment._description_dict())

        return retVal

    def get_all(self):
        """
        This is called by API /admin/overview only
        """
        comments = self.store.find(Comment)

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




