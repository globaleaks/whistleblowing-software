# -*- coding: utf-8
from globaleaks import models
from globaleaks.handlers.admin.step import db_create_step
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import fill_localized_keys
from globaleaks.orm import db_add, db_del, db_get, transact, tw
from globaleaks.rest import requests
from globaleaks.utils.utility import uuid4
import json


def db_create_profile(session,profile_data):
    new_profile = models.Profile()
    new_profile.name = profile_data['name']
    new_profile.description = profile_data['description']
    new_profile.data = json.dumps(profile_data)
    session.add(new_profile)
    session.flush()
    return new_profile


@transact
def create_profile(session, tid,  user_session, request):
    profile = db_create_profile(session, request)
    return serialize_profile(session, profile)

    
def db_get_profiles(session):
    profiles = session.query(models.Profile)
    return [serialize_profile(session, profile) for profile in profiles]


@transact
def get_profiles(session):
    profiles = db_get_profiles(session)
    return profiles


def serialize_profile(session, profile):
     ret = {
        'id': profile.id,
        'name': profile.name,
        'description': profile.description,
        'data':json.loads(profile.data)
    }
     
     return ret

class ProfileCollection(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def post(self):
        validator = requests.AdminProfileDesc
        # validating the request
        request = self.validate_request(self.request.content.read(), validator)
        print("ProfileCollection validate_request", request)
        return create_profile(self.session, request, request)

    def get(self):
        """
        Return all the profiles
        """
        return get_profiles()


class ProfileInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def delete(self, profile_id):
        """
        Delete the specified profile.
        """
        return tw(db_del,
                  models.Profile,
                  (models.Profile.id == profile_id))
    