# -*- coding: utf-8
import re

class UserDetailsFilter:
    def __init__(self, text):
        """Filters the text for any user sensitive information like email, uuid, pgp strings and session ids."""
        self._text = text

    def remove_pgp_formatted_string(self):
        # remove public key block
        self._text = re.sub(r'-----BEGIN.*END.*BLOCK-----', "* filtered pgp string *", self._text, 0, re.DOTALL)

    def remove_session_id_details(self):
        # remove session id details
        self._text = re.sub(r'"session_id".*[a-f0-9]{64}', '"session_id":filtered,', self._text, 0, re.DOTALL)

    def remove_uuid_details(self):
        # Removes the uuid4 details
        self._text = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',
            "* filtered uuid string *", self._text, 0, re.DOTALL)

    def remove_user_email_information(self):
        # removes the email address details
        self._text = re.sub(r'([\w+-.]){0,100}[\w]{1,100}@([\w+-.]){0,100}.[\w]{1,100}',
            "filtered@email", self._text, 0, re.DOTALL)

    def remove_user_sensitive_information(self):
        # removes the user sensitive informations
        self.remove_pgp_formatted_string()
        self.remove_session_id_details()
        self.remove_user_email_information()
        self.remove_uuid_details()

    def filtered_string(self):
        # returns a filtered string after removing all the user sensitive information
        self.remove_user_sensitive_information()
        return self._text

