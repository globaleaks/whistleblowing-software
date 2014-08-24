from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers

from globaleaks.models import Field, FieldGroup, Step, Context, uuid4
from globaleaks.settings import transact, transact_ro
from globaleaks.rest import errors
from globaleaks.utils.structures import Fields

TI_context = {
    'id': unicode(uuid4()),
    # localized stuff
    'name': u'Already localized name',
    'description': u'Already localized desc',
    # fields, usually filled in content by fill_random_fields
    'steps': [ ],
    'selectable_receiver': False,
    'select_all_receivers': True,
    'tip_max_access': 10,
    # tip_timetolive is expressed in days
    'tip_timetolive': 20,
    # submission_timetolive is expressed in hours
    'submission_timetolive': 48,
    'file_max_download' :1,
    'escalation_threshold': 1,
    'receivers' : [],
    'tags': [],
    'file_required': False,
    'receiver_introduction': u'These are our receivers',
    'fields_introduction': u'These are our fields',
    'postpone_superpower': False,
    'can_delete_submission': False,
    'maximum_selectable_receivers': 0,
    'require_file_description': False,
    'delete_consensus_percentage': 0,
    'require_pgp': False,
    'show_small_cards': False,
    'show_receivers': False,
    'presentation_order': 0,
}

TI_field = {

    'preview' : False,
    'stats_enabled' : False,
    'required' : True,
    'type' : 'text area',

    # Supported field types:
    # * radio
    # * checkbox
    # * multiselect
    # * select
    # * input box
    # * text area
    # * modal
    # * dialog
    # * tos

    'regexp' : u'some shit',
    'options': None,

    'default' : u'Go hard ? https://www.youtube.com/watch?v=zc7TGOf-MiI'
}


TI_field_group = {

}

# this need to be moved in /admin/ngfield
def serialize_field(field_storm_obj_):
    import pdb; pdb.set_trace()
    return { ' shit': 1 }

class TestModels(helpers.TestGL):

    receiver_inc = 0

    @transact
    def field_add(self, store):

        field = Field()
        # TODO this has to be optimized with unicode_keys and int_keys in models.py
        field.default = TI_field['default']
        field.type = TI_field['type']
        field.regexp = TI_field['regexp']
        field.required = TI_field['required']
        field.options = TI_field['options']
        store.add(field)

    @transact_ro
    def field_retive(self, store):

        field_list = store.find(Field)
        print "Expected to be 1 = ", len(field_list)

        return serialize_field(field_list[0])


    @inlineCallbacks
    def test_field_store_and_serialize(self):
        yield self.field_add()
        serialized_field = yield self.field_retrive()

        print serialized_field
        self.assertEqual(serialized_field['shit'], TI_field['shit'])

