# -*- coding: utf-8
from globaleaks import models
from globaleaks.handlers.admin.step import db_create_step
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import fill_localized_keys
from globaleaks.orm import db_add, db_del, db_get, transact, tw
from globaleaks.rest import requests
from globaleaks.utils.utility import uuid4


def db_get_profiles(session):
    profiles = session.query(models.Profile)

    print("Profiles get from DB: ==>", profiles)


def db_create_profile(session,profile_data):
    pass



@transact
def create_profile(session, tid, user_session, request, language):
    """
    Updates the specified questionnaire. If the key receivers is specified we remove
    the current receivers of the Questionnaire and reset set it to the new specified
    ones.

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_session: The session of the user performing the operation
    :param request: The request data
    :param language: The language of the request
    :return: A serialized descriptor of the questionnaire
    """
    # profile = db_create_profile(session, tid, user_session, request, language)
    return "hello world"
    # return serialize_questionnaire(session, tid, questionnaire, language)

class ProfileCollection(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def post(self):
        validator = requests.AdminProfileDesc
        # validating the request
        request = self.validate_request(self.request.content.read(), validator)
        print("ProfileCollection validate_request", request)
        return create_profile(self.request.tid, self.session, request, language)
        # return "Profile Imported Succ essfully"

    def get(self):
        """
        Return all the profiles
        """
        return "Hello world!"