# -*- coding: utf-8
import os
import re
import sys

class UserDetailsFilter:
    def __init__(self, text):
        self._text = text

    def remove_bgp_formatted_string(self):
        # remove public key block
        self._text = re.sub(r'-----BEGIN PGP PUBLIC KEY BLOCK-----.*-----END PGP PUBLIC KEY BLOCK-----',
            "*****", self._text, 0, re.DOTALL)

        # remove private key block
        self._text = re.sub(r'-----BEGIN PGP PRIVATE KEY BLOCK-----.*-----END PGP PRIVATE KEY BLOCK-----',
            "*****", self._text, 0, re.DOTALL)


    def remove_session_id_details(self):
        # remove session id details
        # here the assumption is that json output session details
        # may look something like this:
        #   {...., "session_id": .... } or  {...., "session_id": .... , .... }

        self._text = re.sub(r'"session_id":.*,', '"***":***,', self._text, 0, re.DOTALL)
        self._text = re.sub(r'"session_id":.*}', '"***":***}', self._text, 0, re.DOTALL)


    def remove_uuid_details(self):
        # Removes the uuid4 details
        self._text = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',
            "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", self._text, 0, re.DOTALL)

    def remove_user_email_information(self):
        # removes the email address details
        self._text = re.sub(r'([\w+-.]){0,100}[\w]{1,100}@([\w+-.]){0,100}.[\w]{1,100}',
            "~~~~~~@~~~~~~", self._text, 0, re.DOTALL)

    def remove_user_sensitive_information(self):
        # removes the user sensitive informations
        self.remove_bgp_formatted_string()
        self.remove_session_id_details()
        self.remove_user_email_information()
        self.remove_uuid_details()

    def filtered_string(self):
        # returns a filtered string after removing all the user sensitive information
        self.remove_user_sensitive_information()
        return self._text

