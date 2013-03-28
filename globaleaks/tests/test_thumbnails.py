import os
import random
import uuid
from PIL import Image, ImageDraw
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admstaticfiles import reserved_name_check, import_node_logo, import_receiver_pic
from globaleaks.settings import GLSetting
from globaleaks.rest import errors
from globaleaks.handlers.admin import create_receiver
from globaleaks.tests import helpers


class TestThumbnails(helpers.TestWithDB):

    def mock_settings(self):
        GLSetting.static_path = os.getcwd()

    def generate_random_png_400x400(self):
        """
        testing utility used to generate a valid pic path
        """
        img = Image.new("RGB", (400,400), "#FFFFFF")
        draw = ImageDraw.Draw(img)

        for i in range(400):
            draw.line((i,0,i,300), fill=(int(i % 200), int(i % 150), int(i % 100)))

        fname = "testfile_%d.png" % random.randint(1, 999)
        fpath = os.path.join(GLSetting.static_path, fname)
        img.save(fpath, "PNG")

        fake_filedesc = { 'filename': fname,
                          'content_type': 'useless',
                          'size': 'unknow/useless',
                          '_gl_file_path': fpath
                          }
        return fake_filedesc

    def generate_fake_data(self):

        fname = "a_random_bunch_of_data_%d.png" % random.randint(1, 9999)
        fpath = os.path.join(GLSetting.static_path, fname)

        with open(fname, "w+") as fd:
            fd.write(os.urandom(4000))

        fake_filedesc = { 'filename': fname,
                          'content_type': 'useless',
                          'size': 'unknow/useless',
                          '_gl_file_path': fpath
        }
        return fake_filedesc


    def check_generated_image(self, axis, fpath):
        img_input = Image.open(fpath)
        self.assertEqual(img_input.size,(axis, axis))

    def test_good_system_logo(self):
        self.mock_settings()
        dummy_image = self.generate_random_png_400x400()
        import_node_logo(dummy_image)
        expected_path = os.path.join(GLSetting.static_path, "%s.png" % GLSetting.reserved_nodelogo_name)
        self.check_generated_image(140, expected_path)

    def test_bad_system_logo(self):
        self.mock_settings()
        bad_dummy_image = self.generate_fake_data()
        self.assertRaises( IOError, import_node_logo, bad_dummy_image )

    def test_reserverd_name_check(self):
        logo_reserved = GLSetting.reserved_nodelogo_name
        self.assertTrue(reserved_name_check(logo_reserved))
        receiver_format_reserved = unicode(uuid.uuid4())
        self.assertTrue(reserved_name_check(receiver_format_reserved))

        reserved_with_stuff_after_1 = "%s.whatever" % GLSetting.reserved_nodelogo_name
        self.assertRaises(errors.ReservedFileName,
                          reserved_name_check,
                          reserved_with_stuff_after_1)
        reserved_with_stuff_after_2 = "%s.whatever" % unicode(uuid.uuid4())
        self.assertRaises(errors.ReservedFileName,
                          reserved_name_check,
                          reserved_with_stuff_after_2)

        innocent_name = receiver_format_reserved[2:]
        self.assertFalse(reserved_name_check(innocent_name))

    @inlineCallbacks
    def test_good_receiver_portrait(self):
        self.mock_settings()
        dummyReceiver = {
            'notification_fields': {'mail_address': u'first@winstonsmith.org' },
            'name': u'first', 'description': u"I'm tha 1st",
            'receiver_level': u'1', 'can_delete_submission': True,
            'password': "DUMMYPAZZWORZ",
        }
        receiver_desc = yield create_receiver(dummyReceiver)

        dummy_image = self.generate_random_png_400x400()
        receiver_name = yield import_receiver_pic(dummy_image,
                                                  receiver_desc['receiver_gus'])

        self.assertEqual(receiver_name, dummyReceiver['name'])

        self.check_generated_image(120,
                os.path.join( GLSetting.static_path,
                              "%s_120.png" % receiver_desc['receiver_gus']
                )
            )
        self.check_generated_image(40,
                os.path.join( GLSetting.static_path,
                    "%s_40.png" % receiver_desc['receiver_gus']
                )
            )



    def test_bad_UUID_receiver_portrait(self):
        self.mock_settings()
        dummy_image = self.generate_random_png_400x400()
        fake_rcvr_uuid = unicode(uuid.uuid4())
        try:
            yield import_receiver_pic(dummy_image, fake_rcvr_uuid)
            self.assertTrue(False)
        except errors.ReceiverGusNotFound:
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)


    def test_bad_image_receiver_portrait(self):
        pass



