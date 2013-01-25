# -*- coding: UTF-8
#
#   file_process
#   ************
#
# FileProcess is the scheduled operators that perform validation in the submitted file.
# the profiles present would be configured by Administrator, and no receiver settings
# are present.


from globaleaks import config
from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.models.externaltip import File
from globaleaks.models.options import PluginProfiles
from globaleaks.plugins.manager import PluginManager
from twisted.internet.defer import inlineCallbacks
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.submission import Submission
from datetime import datetime, date
import os

__all__ = ['APSFileProcess']


class APSFileProcess(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is to check all the new files and validate
        thru the configured SystemSettings

        possible marker in the file are:
            'not processed', 'ready', 'blocked', 'stored'
        defined in File._marker

        """
        plugin_type = u'fileprocess'

        file_iface = File()
        profile_iface = PluginProfiles()

        not_processed_file = yield file_iface.get_file_by_marker(file_iface._marker[0])

        print "FileProcess", not_processed_file

        for single_file in not_processed_file:

            profile_associated = yield profile_iface.get_profiles_by_contexts([ single_file['context_gus'] ] )

            for p_cfg in profile_associated:

                if p_cfg['plugin_type'] != plugin_type:
                    continue

                print "processing", single_file['file_name'], "using the profile", p_cfg['profile_gus'], "configured for", p_cfg['plugin_name']
                plugin = PluginManager.instance_plugin(p_cfg['plugin_name'])

                try:
                    tempfpath = os.path.join(config.advanced.submissions_dir, single_file['file_gus'])
                except AttributeError:
                    # XXX hi level danger Log - no directory present to perform file analysis
                    continue

                return_code = plugin.do_fileprocess(tempfpath, p_cfg['admin_settings'])

                # Todo Log/stats in both cases
                if return_code:
                    yield file_iface.flip_mark(single_file['file_gus'], file_iface._marker[1]) # ready
                else:
                    yield file_iface.flip_mark(single_file['file_gus'], file_iface._marker[2]) # blocked
