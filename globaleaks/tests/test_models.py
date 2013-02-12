from twisted.internet.defer import inlineCallbacks

from globaleaks.models import Context, Receiver, Folder, InternalFile
from globaleaks.db import tables
from globaleaks.settings import transact
from globaleaks.tests import helpers

class TestModels(helpers.TestHandler):
    def setUp(self):
        return self._setup_database()

    @transact
    def _setup_database(self):
        self.store.execute(tables.generateCreateQuery(Context))
        self.store.execute(tables.generateCreateQuery(Receiver))
        self.store.execute(tables.generateCreateQuery(Folder))
        self.store.execute(tables.generateCreateQuery(InternalFile))

    @transact
    def create_context_with_receivers(self):
        context = Context()
        receiver1 = Receiver()
        receiver2 = Receiver()
        context.receivers.add(receiver1)
        context.receivers.add(receiver2)
        self.store.add(context)
        return context.id

    @transact
    def create_folder_with_files(self):
        file1 = InternalFile()
        file2 = InternalFile()
        self.store.add(file1)
        self.store.add(file2)

        folder = Folder()
        folder.files.add(file1)
        folder.files.add(file2)
        self.store.add(folder)
        return folder.id

    @transact
    def list_receivers_of_context(self, context_id):
        context = self.store.find(Context, Context.id == context_id).one()
        receivers = []
        for receiver in context.receivers:
            receivers.append(receiver.id)
        return receivers

    @transact
    def list_files_of_folder(self, folder_id):
        folder = self.store.find(Folder, Folder.id == folder_id).one()
        files = []
        for file in folder.files:
            files.append(file.id)
        return files

    @inlineCallbacks
    def test_context_receiver_reference(self):
        context_id = yield self.create_context_with_receivers()
        receivers = yield self.list_receivers_of_context(context_id)
        self.assertEqual(2, len(receivers))

    @inlineCallbacks
    def test_folder_receiver_reference_set(self):
        context_id = yield self.create_folder_with_files()
        files = yield self.list_files_of_folder(context_id)
        self.assertEqual(2, len(files))

