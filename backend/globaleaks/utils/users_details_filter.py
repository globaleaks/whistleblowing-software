# -*- coding: utf-8
import os
import re
import sys
import traceback
from log import log

class UserDetailsFilter:
    def __init__(self, text):
        self._text = text
    
    def remove_bgp_formatted_string(self):
        try:
            # remove public key block
            self._text = re.sub(r'-----BEGIN PGP PUBLIC KEY BLOCK-----.*-----END PGP PUBLIC KEY BLOCK-----',\
                "*****", self._text, 0, re.DOTALL)

            # remove private key block
            self._text = re.sub(r'-----BEGIN PGP PRIVATE KEY BLOCK-----.*-----END PGP PRIVATE KEY BLOCK-----',\
                "*****", self._text, 0, re.DOTALL)

        except Exception as e:
            log.err('Unable to replace the bgp formatted string %s .: %s', self._text, exception)
            log.err('Verbose exception traceback:')
            etype, value, tback = sys.exc_info()
            log.err('\n'.join(traceback.format_exception(etype, value, tback)))

    def remove_session_id_details(self):
        try:
            # remove session id details
            # here the assumption is that json output session details
            # may look something like this:
            #   {...., "session_id": .... } or  {...., "session_id": .... , .... } 

            self._text = re.sub(r'session_id":.*,', "*****", self._text, 0, re.DOTALL)
            self._text = re.sub(r'session_id":.*}', "*****", self._text, 0, re.DOTALL)                        
        
        except Exception as e:
            log.err('Unable to replace the session_id string %s .: %s', self._text, exception)
            log.err('Verbose exception traceback:')
            etype, value, tback = sys.exc_info()
            log.err('\n'.join(traceback.format_exception(etype, value, tback)))

    def remove_uuid_details(self):
        try:
            self._text = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',\
                "*****", self._text, 0, re.DOTALL)

        except Exception as e:
            log.err('Unable to replace the uuid string %s .: %s', self._text, exception)
            log.err('Verbose exception traceback:')
            etype, value, tback = sys.exc_info()
            log.err('\n'.join(traceback.format_exception(etype, value, tback)))

    def remove_user_email_information(self):
        try:
            self._text = re.sub(r'([\w+-.]){0,100}[\w]{1,100}@([\w+-.]){0,100}.[\w]{1,100}',\
                "*****", self._text, 0, re.DOTALL)

        except Exception as e:
            log.err('Unable to replace the email id string %s .: %s', self._text, exception)
            log.err('Verbose exception traceback:')
            etype, value, tback = sys.exc_info()
            log.err('\n'.join(traceback.format_exception(etype, value, tback)))


    def remove_user_sensitive_information(self):
        self.remove_bgp_formatted_string()
        self.remove_session_id_details()
        self.remove_user_email_information()
        self.remove_uuid_details()
    
    def filtered_string(self):
        self.remove_user_sensitive_information()
        return self._text

