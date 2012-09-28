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
    # return 'ID'+seed+'_'+str(counter)
    return 'ID'+str(counter)

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

moduleDataDict=dict({"ID": randomID('module'), "active": False, "type": "string",
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
# U1-U5, T1-T6, R1-R2, A1-A4, Tip external
# 
# U1 `/node/`                                           (test implemented)
# U2 `/submission`
# U3 `/submission/<submission_id>`
# U4 `/submission/<submission_id>/finalize`
# U5 `/submission/<submission_id>/upload_file`

# T1 `/tip/<string auth t_id>`
# T2 `/tip/<uniq_Tip_$ID>/add_comment`
# T3 `/tip/<uniq_Tip_$ID>/update_file`
# T4 `/tip/<string t_id>/finalize_update`
# T5 `/tip/<string t_id>/download_material`
# T6 `/tip/<string t_id>/pertinence`

# R1 `/receiver/<string t_id>/overview`
# R2 `/receiver/<string module_name><string t_id>/module`

# A1 `/admin/node/`                                       (test implemented)
# A2 `/admin/contexts/`                                   (test implemented)
# A3 `/admin/receivers/<context_$ID>/`                    (test implemented)
# A4 `/admin/modules/<context_$ID>/<string module_type>/` (test implemented)

#
# THIS REFERENCE IS PRESENT IN:
# http://github.com/globaleaks/GlobaLeaks/wiki/API-Specification
# globaleaks/rest/*.py code
# 

"""
whistlist:

testBlock = restDummy('A4', [GET|POST|PUT|DELETE], uriargs)

testBlock['method'], 'request', 'url', 'result'
request and result are not dict, but GLOD (extending OD), with
 comparation checks (do not compare content, but format)
 type validation with regexp


issues:
--- Arturo would begone crazy if I use A4 as index
--- I would be crazy if I've to grep "/admin/modules/" for debug

"""

testDict = dict()

testDict['U1'] = [ ({
        'method' : 'GET',
        'request' : False,
        'url' : '/node',
        'expected_result' : ({ "name": "string", "statistics": nodeStatisticsDict, 
                               "node_properties": nodePropertiesDict,
                               "contexts": [ contextDescriptionDict ],
                               "description": localizationDict('nodeDesc'),
                               "public_site": "string", "hidden_service": "string", "url_schema": "string" })
        }) ]

testDict['U2'] = [ ({
        'method' : 'GET',
        'request': False,
        'url' : '/submission',
        'expected_result': ({ 'submission-ID' : 'string', 'creation-Time': 'Time' })
    }) ]

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
        'url' : '/admin/node',
        'expected_result' : A1_recurring_result
        }), ({
        'method': 'POST',
        'request' : ({
                  'name': 'A1_string',
                  'node_properties': nodePropertiesDict,
                  'description': localizationDict,
                  'public_site': 'string',
                  'hidden_service': 'string',
                  'url_schema': 'string',
                  'enable_stats': 'StatsThatNeedToBeDefinedBeforeChooseWhichHasToBeEnabledAndWhichMustNot',
                  'do_leakdirectory_update': True,
                  'new_admin_password': 'string' }),
        'url' : '/admin/node',
        'expected_result' : A1_recurring_result
        }) ]

A2_recurring_result = dict ({"contexts": [ contextDescriptionDict, contextDescriptionDict ] })
testDict['A2'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url' : '/admin/contexts/' + randomID('context_A2'),
        'expected_result' : A2_recurring_result
        }), ({
        'method': 'PUT',
        'request' : ({ "context": contextDescriptionDict }),
        'url' : '/admin/contexts/' + randomID('context_A2'),
        'expected_result' : A2_recurring_result
        }), ({
        'method': 'DELETE',
        'request' : ({ "context": contextDescriptionDict }),
        'url' : '/admin/contexts/' + randomID('context_A2'),
        'expected_result' : A2_recurring_result
        }) ]

# test the fallback of post_hack and approriate error handling
testDict['A2F'] = [
        ({
        'method': 'POST',
        'request' : ({ 'method': 'put', "context": contextDescriptionDict }),
        'url' : '/admin/contexts/' + randomID('contextwrappedput_A2'),
        'expected_result' : A2_recurring_result
        }), ({
        'method': 'POST',
        'request' : ({ 'method': 'delete', "context": contextDescriptionDict }),
        'url' : '/admin/contexts/' + randomID('contextwrappeddelete_A2'),
        'expected_result' : A2_recurring_result
        }) ]


A3_recurring_result = dict ({ "receivers": [ receiverDescriptionDict, receiverDescriptionDict ] })

testDict['A3'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url' : '/admin/receivers/' + randomID('receiver_A3'),
        'expected_result' : A3_recurring_result
        }), ({
        'method': 'PUT',
        'request' : ({ "receiver": receiverDescriptionDict }),
        'url' : '/admin/receivers/' + randomID('receiver_A3'),
        'expected_result' : A3_recurring_result
        }), ({
        'method': 'POST',
        'request' : ({ "put": True, "delete": False, "receiver": receiverDescriptionDict }),
        'url' : '/admin/receivers/' + randomID('receiver_A3'),
        'expected_result' : A3_recurring_result
        }), ({
        'method': 'DELETE',
        'request' : ({ "receiver": receiverDescriptionDict }),
        'url' : '/admin/receivers/' + randomID('receiver_A3'),
        r'expected_result' : A3_recurring_result
        }) ]

A4_recurring_result = dict ({
        "modules_available": [ moduleDataDict, moduleDataDict, ]
     })

def A4_url(moduletype):
    return '/admin/modules/' +  randomID('context_A4') + '/' + moduletype

testDict['A4'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url' : A4_url('notification'),
        'expected_result' : A4_recurring_result,
        }), ({
        'method': 'POST',
        'request' : ({  "module": moduleDataDict  }),
        'url' : A4_url('notification'),
        'expected_result' : A4_recurring_result,
        }), ({
        'method': 'GET',
        'request' : False,
        'url' : A4_url('delivery'),
        'expected_result' : A4_recurring_result,
        }), ({
        'method': 'POST',
        'request' : ({  "module": moduleDataDict  }),
        'url' : A4_url('delivery'),
        'expected_result' : A4_recurring_result,
        }), ({
        'method': 'GET',
        'request' : False,
        'url' : A4_url('inputfilter'),
        'expected_result' : A4_recurring_result,
        }), ({
        'method': 'POST',
        'request' : ({  "module": moduleDataDict  }),
        'url' : A4_url('inputfilter'),
        'expected_result' : A4_recurring_result,
        }) ]


R1_recurring_result = dict ({
        "tips": [ tipIndexDict, tipIndexDict ],
        "notification": [ moduleDataDict, moduleDataDict ],
        "delivery": [ moduleDataDict, moduleDataDict ],
        "properties": [ receiverDescriptionDict ],
     })

testDict['R1'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url' : '/receiver/' + randomID('Tip_ID_R1'),
        'expected_result' : R1_recurring_result,
        }) ]

R2_recurring_result = dict ({
        "notification": [ moduleDataDict, moduleDataDict ],
        "delivery": [ moduleDataDict, moduleDataDict ],
     })

def url_R2(moduletype):
    return '/receiver/' + randomID('TIPID_R2') + '/' + moduletype

testDict['R2'] = [
        ({
        'method': 'GET',
        'request' : False,
        'url': url_R2('notification'),
        'expected_result' : R2_recurring_result,
        }), ({
        'method': 'GET',
        'request' : False,
        'url': url_R2('delivery'),
        'expected_result' : R2_recurring_result,
        }), ({
        'method': 'PUT',
        'request' : ({ "module": moduleDataDict }),
        'url': url_R2('notification'),
        'expected_result' : R2_recurring_result,
        }), ({
        'method': 'PUT',
        'request' : ({ "module": moduleDataDict }),
        'url': url_R2('delivery'),
        'expected_result' : R2_recurring_result,
        }), ({
        'method': 'POST',
        'request' : ({ "method": 'delete', "module": moduleDataDict }),
        'url': url_R2('notification'),
        'expected_result' : R2_recurring_result,
        }), ({
        'method': 'POST',
        'request' : ({ "method": 'put', "module": moduleDataDict }),
        'url': url_R2('delivery'),
        'expected_result' : R2_recurring_result,
        }), ({
        'method': 'POST',
        'request' : ({ "method": 'delete', "module": moduleDataDict }),
        'url': url_R2('notification'),
        'expected_result' : R2_recurring_result,
        }), ({
        'method': 'POST',
        'request' : ({ "method": 'put', "module": moduleDataDict }),
        'url': url_R2('delivery'),
        'expected_result' : R2_recurring_result,
        }), ({
        'method': 'DELETE',
        'request' : ({ "module": moduleDataDict }),
        'url': url_R2('notification'),
        'expected_result' : R2_recurring_result,
        }), ({
        'method': 'DELETE',
        'request' : ({ "module": moduleDataDict }),
        'url': url_R2('delivery'),
        'expected_result' : R2_recurring_result,
        }) ]




def do_curl(url, method, not_encoded_parm=''):
    params = urllib.urlencode(not_encoded_parm)
    headers = {
     "Content-type": "application/x-www-form-urlencoded",
     "Accept": "text/plain",
     "Accept": "application/json"
              }

    import time
    time.sleep(0.2)
    conn = httplib.HTTPConnection(baseurl)

    if checkOpt('request'):
        print "[+] CONNECTION REQUEST:", method, baseurl, url, params, headers,"\n"

    conn.request(method, url, params, headers)

    response = conn.getresponse()

    if checkOpt('response'):
        print "[+] RESPONSE:", response.read(),"\n"

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

def checkOpt(option):

    for arg in sys.argv:
        if arg == option:
            return True

    return False

class myUnitTest(unittest.TestCase):

    def do_METHOD(self, method, restName):

        dictID = restName + '_' + method
        test_sets = testDict[restName]

        for i, x in enumerate(testDict[restName]):
            if x['method'] == method:
                settings = x

                print "[do_METHOD] testing", restName, "method", method, "in", settings['url']
                if checkOpt('request') or checkOpt('verbose'):
                    print "[do_METHOD]", i," using url", settings['url'], "request", settings['request']

                if checkOpt('verbose'):
                    clean_debug(1, settings)

                if method == 'GET':
                    result = do_curl(settings['url'], settings['method'])
                else:
                    result = do_curl(settings['url'], settings['method'], settings['request'] )

                if checkOpt('verbose'):
                    clean_debug(1, result)


class U1(myUnitTest):

    def do_tests(self):
        self.do_METHOD('GET', 'U1')

class U2(myUnitTest):

    def do_tests(self):
        self.do_METHOD('GET', 'U2')

class A1(myUnitTest):
    def do_tests(self):
        self.do_METHOD('GET', 'A1')
        self.do_METHOD('POST', 'A1')

class A2(myUnitTest):
    def do_tests(self):
        self.do_METHOD('PUT', 'A2')
        self.do_METHOD('GET', 'A2')
        self.do_METHOD('DELETE', 'A2')

        # do_METHOD loops over all the three POSTs
        self.do_METHOD('POST', 'A2F')

class A3(myUnitTest):
    def do_tests(self):
        self.do_METHOD('PUT', 'A3')
        self.do_METHOD('GET', 'A3')
        self.do_METHOD('POST', 'A3')
        self.do_METHOD('DELETE', 'A3')

class A4(myUnitTest):
    def do_tests(self):
        self.do_METHOD('GET', 'A4')
        self.do_METHOD('POST', 'A4')

class R1(myUnitTest):
    def do_tests(self):
        self.do_METHOD('GET', 'R1')

class R2(myUnitTest):
    def do_tests(self):
        # loop in all the extended /{notification|delivery}/
        self.do_METHOD('GET', 'R2')
        self.do_METHOD('PUT', 'R2')
        self.do_METHOD('POST', 'R2')
        self.do_METHOD('DELETE', 'R2')


# HERE START THE TEST

if len(sys.argv) >= 2:
    for x in enumerate(sys.argv):
        if x[1].find(':') != -1:
            baseurl = x[1]

print "starting tests to:", baseurl

if checkOpt('verbose'):
    print "verbose is ON (imply response, request and some other details)"
if checkOpt('response'):
    print "Response verbosity printing is ON"
if checkOpt('request'):
    print "Request verbosity printing is ON"


U1().do_tests()
U2().do_tests()

A1().do_tests()
A2().do_tests()
A3().do_tests()
# A4().do_tests()

R1().do_tests()
R2().do_tests()


