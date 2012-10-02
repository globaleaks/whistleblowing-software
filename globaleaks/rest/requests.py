# -*- coding: UTF-8
#   Requests 
#   ********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   This file contain the definition of all the requests struct perfomed to GLB
#   is used by curteg client (for compose the requests) and by GLB (to sanitize having the
#   right structured code)

from globaleaks.utils import recurringtypes as GLT


# U3 (POST)
class submissionUpdate(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)

        self.define_array("fields", GLT.formFieldsDict() )
        self.define_array("receiver_selected", 'receiverID')


# U4 (POST)
class finalizeSubmission(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)

        self.define("proposed_receipt", "string")
        self.define("folder_name", "string")
        self.define("folder_description", "string")

# U5 (file, CURD) -- not yet defined

# T1 (POST) - receiver only
class tipOperations(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)
        self.define("personal_delete", "bool")
        self.define("submission_delete", "bool")
        self.define("escalate", "bool")

# T2 (POST)
class sendComment(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)
        self.define("comment", GLT.commentDescriptionDict() )

# T3 (files) -- not yet defined

# T4 (POST - finalize Folder upload)
class finalizeIntegration(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)
        self.define("folder_name", "string")
        self.define("folder_description", "string")

# T6 (POST) - receiver only
class pertinenceVote(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)
        self.define("pertinence", "int")

# R2 (CURD)
class receiverOptions(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)

        # self.support_POST_hack()
        # XXX
        self.define("module", GLT.moduleDataDict() )

# A1 (POST)
class nodeAdminSetup(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)

        self.define("name", "string")
        self.define("admin_statistics_ratio", "int")
        self.define("public_statistics_ratio", "int")
        self.define("node_properties", GLT.nodePropertiesDict() )

        self.define("node_description", "string")
            # GLT.localizationDict() )
            # XXX may exists different description fields, like "about us"
            # "privacy policy" and the other in the footer
            # also logo upload need to be handled

        self.define("public_site", "string")
        self.define("hidden_service", "string")
        self.define("url_schema", "string")

        self.define("do_leakdirectory_update", "bool")
        self.define("new_admin_password", "string")

# A2 (CURD)
class contextConfiguration(GLT.GLTypes):

    def __init__(self):
        GLT.GLTypes.__init__(self, self.__class__.__name__)

        # self.support_POST_hack()
        # XXX
        self.define("context", GLT.contextDescriptionDict() )

# A3 (CURD)
class receiverConfiguration(GLT.GLTypes):

    def __init__(self):
        GLT.GLTypes.__init__(self, self.__class__.__name__)

        # self.support_POST_hack()
        # XXX
        self.define("receiver", GLT.receiverDescriptionDict() )

# A4 (POST)
class moduleConfiguration(GLT.GLTypes):

    def __init__(self):
        GLT.GLTypes.__init__(self, self.__class__.__name__)

        self.define("module", GLT.moduleDataDict() )
            #  align with the API


