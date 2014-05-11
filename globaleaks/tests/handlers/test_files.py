# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers import files
from globaleaks.settings import GLSetting
from globaleaks.security import GLSecureTemporaryFile


class TestFileAdd(helpers.TestHandler):
    _handler = files.FileAdd

    @inlineCallbacks
    def test_001_post(self):

        temporary_file = GLSecureTemporaryFile(GLSetting.tmp_upload_path)
        temporary_file.write("ANTANI")
        temporary_file.avoid_delete()

        request_body = {
            'body': temporary_file,
            'body_len': len("ANTANI"),
            'body_filepath': temporary_file.filepath,
            'filename': 'valid.blabla',
            'content_type': 'text/plain'
        }

        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb', body=request_body)
            handler.current_user['user_id'] = wbtip_desc['wbtip_id']
            yield handler.post()

class TestDownload(helpers.TestHandler):
    _handler = files.Download

    @inlineCallbacks
    def test_001_post(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            rfiles_desc = yield self.get_rfiles(rtip_desc['rtip_id'])
            for rfile_desc in rfiles_desc:
                handler = self.request(role='receiver')
                handler.current_user['user_id'] = rtip_desc['receiver_id']
                yield handler.post(rtip_desc['rtip_id'], rfile_desc['rfile_id'])

class TestCSSStaticFileHandler(helpers.TestHandler):
    _handler = files.CSSStaticFileHandler

    @inlineCallbacks
    def test_001_get(self):
        handler = self.request({},
                               kwargs={'path': GLSetting.static_path,
                                       'default_filename': '/static/custom_stylesheet.css'})

        yield handler.get("custom_stylesheet.css")
