# -*- coding: UTF-8
#   api
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE file
#
#   Contains all the logic for handling tip related operations.
#   This contains the specification of the API.
#   Read this if you want to have an overall view of what API calls are handled
#   by what.

from cyclone.web import StaticFileHandler

from globaleaks import config
from globaleaks.handlers import node, submission, tip, admin, receiver, files
from globaleaks.messages.base import tipGUS, contextGUS

more_lax = r'(\w+)' # XXX need to be changed with regexp.submission_gus | regexp.receipt_gus
not_defined_regexp = r'(\w+)'
receiver_token_auth = r'(\w+)' # This would cover regexp.tip_gus | regexp.welcome_token_gus

# Here is mapped a path and the associated class to be invoked,
# Three kind of Classes can be distigued:
# * Crud (SubmissionCrud, FileCrud, etc)
#   supports a complete CRUD (PUT, POST, DELETE, GET)
# * Management (TipManagement, ReceiverManagement)
#   supports operation of interaction (GET, PUT), Never Creation (POST) and maybe Delete
# * Available
#   supports only GET operation, returning a list of elements

spec = [
    ## Node Handler ##
    #  * /node U1
    (r'/node', node.InfoAvailable),

    ## Submission Handlers ##
    #  * /submission/ U2
    (r'/submission/' + contextGUS.regexp + '/new', submission.SubmissionCrud),

    #  * /file/ U3
    (r'/file/', files.FileCrud),

    # * /statistics/ U4
    (r'/statistics/', node.StatsAvailable),

    ## Tip Handlers ##
    #  * /tip/<tip_GUS>/ T1
    (r'/tip/' + more_lax, tip.TipManagement),

    ## Receiver Handlers ##
    #  * /reciever/<receiver_token_auth>/management R1
    (r'/receiver/' + receiver_token_auth + '/management', receiver.ReceiverManagement),

    #  * /receiver/<receiver_token_auth>/pluginprofiles R2
    (r'/receiver/' + tipGUS.regexp + '/pluginprofiles', receiver.ProfilesAvailable),

    #  * /receiver/<tip_GUS>/plugin R3
    (r'/receiver/' + tipGUS.regexp + '/plugin/', receiver.PluginCrud),

    ## Admin Handlers ##
    #  * /admin/node A1
    (r'/admin/node', admin.NodeManagement),

    #  * /admin/contexts/ A2
    (r'/admin/contexts/', admin.ContextsAvailable),

    #  * /admin/context/ A3
    (r'/admin/context/', admin.ContextCrud),

    #  * /admin/receivers/ A4
    (r'/admin/receivers/', admin.ReceiversAvailable),

    #  * /admin/receiver/ A5
    (r'/admin/receiver/', admin.ReceiverCrud),

    #  * /admin/plugins/ A6
    (r'/admin/plugins/', admin.PluginsAvailable),

    #  * /admin/profile/ A7
    (r'/admin/profile/', admin.ProfilesCrud),

    #  * /admin/statistics/ A8
    (r'/admin/statistics/', admin.StatisticsAvailable),

    #  * /admin/overview A9
    (r'/admin/overview/' + not_defined_regexp, admin.EntryAvailable),

    #  * /admin/tasks/ AA
    (r'/admin/tasks/' + not_defined_regexp, admin.TaskManagement),

    ## Main Web app ##
    # * /
    (r'/(.*)', StaticFileHandler, {'path': config.main.glclient_path})
]

