from twisted.trial import unittest
import httplib, urllib, httplib2
import json
import sys


"""
This value is changed using a first argument of host:port
"""
baseurl = "127.0.0.1:8082"

"""
Generic object definition
"""

counter = 0
def randomID(seed):
    global counter
    counter += 1
    return 'ID_'+seed+'_'+str(counter)

def localizationDict(seed):
    global counter
    counter += 1
    return dict({ "IT" : 'IT_'+seed+'_'+str(counter), "EN" : 'EN_'+seed+'_'+str(counter), "FR" : 'FR_'+seed+'_'+str(counter) })

localizationArray=["IT", "EN", "FR"]

fileDict=dict({"filename": "string", "comment": "string", "size": 1234, "content_type": "string", "date": "Time", "CleanedMetaData": 1234 })

formFieldsDict=dict({ "element-name": "string", "element-type": "Enum", "default-value": "string", "required": False })

receiverDescriptionDict=dict({   "ReceiverID": randomID('receiver'), "CanDeleteSubmission": False, 
            "CanPostponeExpiration": False, "CanConfigureNotification": False, "CanConfigureDelivery": False, 
            "receiver_name": "string", "receiver_description": "string",
            "receiver_tags": "string", "contact_data": "string", "creation_date": "Time",
            "update_date": "Time", "module_id": randomID('module'),
            "module_dependent_data": formFieldsDict, "module_dependent_stats": "Array" })

nodePropertiesDict=dict({   "AnonymousSubmissionOnly": False, "AdminAreReceivers": False, "NodeProvideDocsPublication": False,
            "FixedCorpusOfReceiver": False, "ReceiverAreAnonymous": False })

moduleDataDict=({"ID": randomID('module'), "active": False, "type": "string",
            "name": "string", "description": "string", "admin_options": formFieldsDict, 
            "user_options": formFieldsDict,  "service_message": "string" })

groupDescriptionDict=dict({ "group_id" : randomID('group'), "group_name": "string", "description" : localizationDict('groupDesc'),
            "spoken_language": localizationArray, "group_tags": "string", 
            "receiver_list": "Array", "associated_module": moduleDataDict,
            "creation_date": "Time", "update_date": "Time" })

tipStatistics=dict({ "tip_access_ID": randomID('tip_auth'), "tip_title": "string", "last_access": "Time", "last_comment": "Time", "notification_msg": "string",
            "delivery_msg": "string", "expiration_date": "Time", "pertinence_overall": 1234, "requested_fields": formFieldsDict,
            "context_name": "string", "group": groupDescriptionDict})

tipIndexDict=dict({ "tip_access_ID": randomID('tip_auth'), "tip_title": "string", "context_ID": randomID('context'), "group_ID": randomID('group'), 
            "notification_adopted": "string", "notification_msg": "string", "delivery_adopted": "string",
            "delivery_msg": "string", "expiration_date": "Time", "creation_date": "Time",
            "update_date": "Time" })
contextDescriptionDict= dict({ "context_id": randomID('context'), "name": localizationDict('contextDesc'),
            "groups": [ groupDescriptionDict, groupDescriptionDict ],
            "fields": formFieldsDict, "description": "string", "style": "string",
            "creation_date": "Time", "update_date": "Time" })

nodeStatisticsDict=dict({ "something": "toBedefined", "something_other": 12345 })


# REMIND: needed tests are:
# P1-P7, T1-T6, R1-R2, P1-A5, Tip external
# 
# P1 `/node/`                                           (test implemented)
# P2 `/submission`
# P3 `/submission/<submission_id>`
# P4 `/submission/<submission_id>/submit_fields`
# P5 `/submission/<submission_id>/submit_group`
# P6 `/submission/<submission_id>/finalize`
# P7 `/submission/<submission_id>/upload_file`
# T1 `/tip/<string auth t_id>`
# T2 `/tip/<uniq_Tip_$ID>/add_comment`
# T3 `/tip/<uniq_Tip_$ID>/update_file`
# T4 `/tip/<string t_id>/finalize_update`
# T5 `/tip/<string t_id>/download_material`
# T6 `/tip/<string t_id>/pertinence`
# R1 `/receiver/<string t_id>/overview`
# R2 `/receiver/<string t_id>/<string module_name>`
# P1 `/admin/node/`                                     (test implemented)
# A2 `/admin/contexts/`                                 (test implemented)
# A3 `/admin/groups/<context_$ID>/`                     (test implemented)
# A4 `/admin/receivers/<group_$ID>/`                    (test implemented)
# A5 `/admin/modules/<string module_type>/`             (test implemented)

#
# THIS REFERENCE IS PRESENT IN:
# REST-spec.md
# globaleaks/rest/*.py code
# (this file, and all tests)
# github issue tracking
# 
# THEREFORE, EVERY TIME A REST INTERFACE NEED TO BE ADDRESSED OR IMPLEMENTED, ITS
# IMPORTANT USE THE SAME ADDRESSING LOGIC.
 
testDict = dict()

testDict['P1'] = ({
        'method' : 'GET',
        'request' : False,
        'url' : '/node/',
        'expected_result' : ({ "name": "string", "statistics": nodeStatisticsDict, 
                               "node_properties": nodePropertiesDict,
                               "contexts": [ contextDescriptionDict ],
                               "description": localizationDict('nodeDesc'),
                               "public_site": "string", "hidden_service": "string", "url_schema": "string" })
        })

testDict['P2'] = ({
        'method' : 'GET',
        'request': False,
        'url' : '/submission/',
        'expected_result': ({ 'submission-ID' : 'string', 'creation-Time': 'Time' })
    })

A1_recurring_result = dict ({ 
                   'name': 'string',
                   'statistics': nodeStatisticsDict,
                   'private_stats': "PrivateStatToBeDefined",
                   'node_properties': nodePropertiesDict,
                   'contexts': [ contextDescriptionDict, contextDescriptionDict, ],
                   'description': localizationDict,
                   'public_site': 'string',
                   'hidden_service': 'string',
                   'url_schema': 'string' 
                 })

testDict['A1'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url' : '/admin/node/',
        'expected_result' : A1_recurring_result
        }), ({
        'method': 'POST',
        'request' : ({
                  'name': 'string',
                  'node_properties': nodePropertiesDict,
                  'description': localizationDict,
                  'public_site': 'string',
                  'hidden_service': 'string',
                  'url_schema': 'string',
                  'enable_stats': 'StatsThatNeedToBeDefinedBeforeChooseWhichHasToBeEnabledAndWhichMustNot',
                  'do_leakdirectory_update': 'Bool',
                  'new_admin_password': 'string' }),
        'url' : '/admin/node/',
        'expected_result' : A1_recurring_result
        }) ]

A2_recurring_result = dict ({"contexts": [ contextDescriptionDict, contextDescriptionDict ] })
testDict['A2'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url' : '/admin/contexts/' + randomID('contexts'),
        'expected_result' : A2_recurring_result
        }), ({
        'method': 'PUT',
        'request' : ({ "context": contextDescriptionDict }),
        'url' : '/admin/contexts/' + randomID('contexts'),
        'expected_result' : A2_recurring_result
        }), ({
        'method': 'POST',
        'request' : ({ "create": True, "delete": False, "context": contextDescriptionDict }),
        'url' : '/admin/contexts/' + randomID('contexts'),
        'expected_result' : A2_recurring_result
        }), ({
        'method': 'DELETE',
        'request' : ({ "context": contextDescriptionDict }),
        'url' : '/admin/contexts/' + randomID('contexts'),
        'expected_result' : A2_recurring_result
        }) ]

A3_recurring_result = dict ({
        "groups":groupDescriptionDict, 
        "modules_available": [ moduleDataDict, moduleDataDict, ]
     })

testDict['A3'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url' : '/admin/groups/' + randomID('group'),
        'expected_result' : A3_recurring_result
        }), ({
        'method': 'PUT',
        'request' : ({ "group": groupDescriptionDict }),
        'url' : '/admin/groups/' + randomID('group'),
        'expected_result' : A3_recurring_result
        }), ({
        'method': 'POST',
        'request' : ({ "create": True, "delete": False, "group": groupDescriptionDict }),
        'url' : '/admin/groups/' + randomID('group'),
        'expected_result' : A3_recurring_result
        }), ({
        'method': 'DELETE',
        'request' : ({ "group": groupDescriptionDict }),
        'url' : '/admin/groups/' + randomID('group'),
        'expected_result' : A3_recurring_result
        }) ]

A4_recurring_result = dict ({ "receivers": [ receiverDescriptionDict, receiverDescriptionDict ] })
testDict['A4'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url' : '/admin/receiver/' + randomID('receiver'),
        'expected_result' : A4_recurring_result
        }), ({
        'method': 'PUT',
        'request' : ({ "receiver": receiverDescriptionDict }),
        'url' : '/admin/receiver/' + randomID('receiver'),
        'expected_result' : A4_recurring_result
        }), ({
        'method': 'POST',
        'request' : ({ "create": True, "delete": False, "receiver": receiverDescriptionDict }),
        'url' : '/admin/receiver/' + randomID('receiver'),
        'expected_result' : A4_recurring_result
        }), ({
        'method': 'DELETE',
        'request' : ({ "receiver": receiverDescriptionDict }),
        'url' : '/admin/receiver/' + randomID('receiver'),
        'expected_result' : A4_recurring_result
        }) ]

A5_recurring_result = dict ({
        "group_matrix" : 'Array_of_modules-group_application',
        "modules_available": [ moduleDataDict, moduleDataDict, ]
     })

testDict['A5'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url' : '/admin/modules/' + randomID('module-ENUM'),
        'expected_result' : A5_recurring_result,
        }), ({
        'method': 'PUT',
        'request' : ({ "module": moduleDataDict, "group_matrix" : 'Array_of_MGA' }),
        'url' : '/admin/modules/' + randomID('module-ENUM'),
        'expected_result' : A5_recurring_result,
        }), ({
        'method': 'POST',
        'request' : ({ "create": True, "delete": False, "module": moduleDataDict, "group_matrix": 'Array_of_MGA' }),
        'url' : '/admin/modules/' + randomID('module-ENUM'),
        'expected_result' : A5_recurring_result,
        }), ({
        'method': 'DELETE',
        'request' : ({ "module": moduleDataDict }),
        'url' : '/admin/modules/' + randomID('module-ENUM'),
        'expected_result' : A5_recurring_result,
        }) ]

R1_recurring_result = dict ({
        "modules": [ moduleDataDict, moduleDataDict ]
     })

testDict['R1'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url' : '/receiver/' + randomID('Tip-ID') + '/overview',
        'expected_result' : A5_recurring_result,
        }), ({
        'method': 'PUT',
        'request' : ({ "module": moduleDataDict }),
        'url' : '/receiver/' + randomID('Tip-ID') + '/overview',
        'expected_result' : A5_recurring_result,
        }), ({
        'method': 'POST',
        'request' : ({ "create": True, "delete": False, "module": moduleDataDict }),
        'url' : '/receiver/' + randomID('Tip-ID') + '/overview',
        'expected_result' : A5_recurring_result,
        }), ({
        'method': 'DELETE',
        'request' : ({ "module": moduleDataDict }),
        'url' : '/receiver/' + randomID('Tip-ID') + '/overview',
        '}expected_result' : A5_recurring_result,
        }) ]



def do_curl(url, method, not_encoded_parm=''):
    params = urllib.urlencode(not_encoded_parm)
    headers = {
     "Content-type": "application/x-www-form-urlencoded", 
     "Accept": "text/plain", # is useful ? XXX
     "Accept": "application/json" 
              }

    conn = httplib.HTTPConnection(baseurl)
    print "[+] CONNECTION REQUEST:", method, baseurl, url, params, headers,"\n\n"

    conn.request(method, url, params, headers)

    response = conn.getresponse()
    import pdb
    # pdb.set_trace()
    print "[+] RESPONSE:", response.read()

    data = response.read()
    conn.close()

    return data

def clean_debug(rec, targetdict):

    rec += 1

    if not isinstance(targetdict, dict):
        for i in xrange(0, rec): print "\t",
        print "p.s. I'm not a dict", str(targetdict)
        return

    for k, v in targetdict.items():
        if isinstance(v, dict):
            for i in xrange(0, rec): print "\t",
            print k
            clean_debug(rec, v)
        elif type(v) == type([]):
            for elem in v:
                if isinstance(elem, dict):
                    clean_debug(rec, elem)
                else:
                    for i in xrange(0, rec): print "\t",
                    print k," => ", str(elem)

        else:
            for i in xrange(0, rec): print "\t",
            print k," => ", str(v)

class myUnitTest(unittest.TestCase):

    def do_METHOD(self, method, restName):
        print "[do_METHOD] testing", restName, "method", method

        dictID = restName + '_' + method
        test_sets = testDict[restName]

        if not isinstance(testDict[restName], dict):
            for x in testDict[restName]:
                if x['method'] == method:
                    settings = x
        else:
            settings = testDict[restName]

        print "[do_METHOD] using url", settings['url'], "request", settings['request']

        if len(sys.argv) >= 2 and sys.argv[1] == 'verbose':
            clean_debug(1, settings)

        if method == 'GET':
            result = do_curl(settings['url'], settings['method'] )
        else:
            result = do_curl(settings['url'], settings['method'], settings['request'])

        if len(sys.argv) >= 2 and sys.argv[1] == 'verbose':
            clean_debug(1, result)

        # self.assertEqual(result, settings['expected_result'])

class P1(myUnitTest):

    def do_tests(self):
        self.do_METHOD('GET', 'P1')

class P2(myUnitTest):

    def do_tests(self):
        self.do_METHOD('GET', 'P2')

class A1(myUnitTest):
    def do_tests(self):
        self.do_METHOD('GET', 'A1')
        self.do_METHOD('POST', 'A1')

class A2(myUnitTest):
    def do_tests(self):
        self.do_METHOD('PUT', 'A2')
        self.do_METHOD('GET', 'A2')
        self.do_METHOD('POST', 'A2')
        self.do_METHOD('DELETE', 'A2')

class A3(myUnitTest):
    def do_tests(self):
        self.do_METHOD('PUT', 'A3')
        self.do_METHOD('GET', 'A3')
        self.do_METHOD('POST', 'A3')
        self.do_METHOD('DELETE', 'A3')

class A4(myUnitTest):
    def do_tests(self):
        self.do_METHOD('PUT', 'A4')
        self.do_METHOD('GET', 'A4')
        self.do_METHOD('POST', 'A4')
        self.do_METHOD('DELETE', 'A4')

class A5(myUnitTest):
    def do_tests(self):
        self.do_METHOD('PUT', 'A5')
        self.do_METHOD('GET', 'A5')
        self.do_METHOD('POST', 'A5')
        self.do_METHOD('DELETE', 'A5')

class R1(myUnitTest):
    def do_tests(self):
        self.do_METHOD('GET', 'R1')
        self.do_METHOD('PUT', 'R1')
        self.do_METHOD('POST', 'R1')
        self.do_METHOD('DELETE', 'R1')



# HERE START THE TEST

if len(sys.argv) >= 2:
    for x in enumerate(sys.argv):
        if x[1].find(':') != -1:
            baseurl = x[1]
            print "using base url", baseurl
else:
    print "using default base url", baseurl

if len(sys.argv) >= 2 and sys.argv[1] == 'verbose':
    print "verbose modality is ON"
else:
    print "verbose modality is OFF"

P1().do_tests()

A1().do_tests()
A2().do_tests()
A3().do_tests()
A4().do_tests()
A5().do_tests()

R1().do_tests()


