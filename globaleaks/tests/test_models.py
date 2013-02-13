from twisted.internet.defer import inlineCallbacks

from globaleaks.models import Context, Receiver, Folder, InternalFile
from globaleaks.db import tables
from globaleaks.settings import transact
from globaleaks.tests import helpers

class TestModels(helpers.TestHandler):
    def setUp(self):
        return self._setup_database()

    @transact
    def _setup_database(self, store):
        store.execute(tables.generateCreateQuery(Context))
        store.execute(tables.generateCreateQuery(Receiver))
        store.execute(tables.generateCreateQuery(Folder))
        store.execute(tables.generateCreateQuery(InternalFile))

    @transact
    def create_context_with_receivers(self, store):
        context = Context()
        receiver1 = Receiver()
        receiver2 = Receiver()
        context.receivers.add(receiver1)
        context.receivers.add(receiver2)
        store.add(context)
        return context.id

    @transact
    def create_folder_with_files(self, store):
        file1 = InternalFile()
        file2 = InternalFile()
        store.add(file1)
        store.add(file2)

        folder = Folder()
        folder.files.add(file1)
        folder.files.add(file2)
        store.add(folder)
        return folder.id

    @transact
    def create_folder_with_invalid_reference(self, store):
        receiver = Receiver()
        store.add(receiver)

        folder = Folder()
        # Invalid addition to folder.files
        folder.files.add(receiver)
        store.add(folder)
        return folder.id

    @transact
    def create_folder_with_invalid_reference_not_in_store(self, store):
        file1 = InternalFile()

        folder = Folder()
        folder.files.add(file1)
        store.add(folder)
        return folder.id

    @transact
    def create_folder_return_file(self, store):
        file1 = InternalFile()
        file2 = InternalFile()
        store.add(file1)
        store.add(file2)

        folder = Folder()
        folder.files.add(file1)
        folder.files.add(file2)
        store.add(folder)
        return file1.id

    @transact
    def delete_reference(self, store, file_id):
        internal_file = store.find(InternalFile, InternalFile.id == file_id).one()
        store.remove(internal_file)

    @transact
    def list_receivers_of_context(self, store, context_id):
        context = store.find(Context, Context.id == context_id).one()
        receivers = []
        for receiver in context.receivers:
            receivers.append(receiver.id)
        return receivers

    @transact
    def list_files_of_folder(self, store, folder_id):
        folder = store.find(Folder, Folder.id == folder_id).one()
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
        folder_id = yield self.create_folder_with_files()
        files = yield self.list_files_of_folder(folder_id)
        self.assertEqual(2, len(files))

    def test_folder_receiver_invalid_reference_set(self):
        d = self.create_folder_with_invalid_reference()
        self.assertFailure(d, KeyError)
        return d

    @inlineCallbacks
    def test_folder_receiver_invalid_reference_set_not_in_store(self):
        d = self.create_folder_with_invalid_reference_not_in_store()
        return d

    @inlineCallbacks
    def test_delete_reference(self):
        file_id = yield self.create_folder_return_file()
        yield self.delete_reference(file_id)


