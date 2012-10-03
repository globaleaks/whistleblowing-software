import httplib, urllib, httplib2
import sys, os

cwd = '/'.join(__file__.split('/')[:-1])
sys.path.insert(0, os.path.join(cwd, '../'))

from globaleaks.utils.idops import random_submission_id as sID
from globaleaks.utils.idops import random_tip_id as tID
from globaleaks.utils.idops import random_context_id as cID

from globaleaks.rest import answers
from globaleaks.rest import requests
from globaleaks.utils.dummy import dummy_answers
from globaleaks.utils.dummy import dummy_requests

# U1 `/node/`
# U2 `/submission`
# U3 `/submission/<submission_id>`
# U4 `/submission/<submission_id>/finalize`
# U5 `/submission/<submission_id>/upload_file`

# R1 `/receiver/<string t_id>/overview`
# R2 `/receiver/<string module_name><string t_id>/module`

# A1 `/admin/node/`
# A2 `/admin/contexts/`
# A3 `/admin/receivers/<context_$ID>/`
# A4 `/admin/modules/<context_$ID>/<string module_type>/`

# T1 `/tip/<string auth t_id>`
# T2 `/tip/<uniq_Tip_$ID>/add_comment`
# T3 `/tip/<uniq_Tip_$ID>/update_file`
# T4 `/tip/<string t_id>/finalize_update`
# T5 `/tip/<string t_id>/download_material`
# T6 `/tip/<string t_id>/pertinence`

# https://github.com/globaleaks/GlobaLeaks/wiki/API-Specification
# https://github.com/globaleaks/GlobaLeaks/wiki/recurring-data-types


"""
Request schema definition, is derived by a parsing of 
globaleaks.rest.api spec array
"""

schema = {
     "U1" :['/node', ['GET'],'root'],
     "U2" :['/submission', ['GET'],'new'],
     "U3" :['/submission/'+sID()+'/status',['GET','POST'],'status'],
     # "U5" :['/submission/'+sID()+'/files', ['GET','POST','PUT','DELETE'],'files'],
     "U4" :['/submission/'+sID()+'/finalize',['POST'],'finalize'],
     "T1" :['/tip/', ['GET','POST'],'tip'],
     "T2" :['/tip/'+tID()+'/comment', ['POST'],'comment'],
     # "T3" :['/tip/'+tID()+'/files', ['GET','POST','PUT','DELETE'],'tipfiles'],
     "T4" :['/tip/'+tID()+'/finalize', ['POST'],'tipfinalize'],
     "T5" :['/tip/'+tID()+'/download', ['GET'],'download'],
     "T6" :['/tip/'+tID()+'/pertinence', ['GET'],'pertinence'],
     "R1" :['/receiver/' + tID(), ['GET'],'receiver'],
     "R2" :['/receiver/' + tID() +'/notification', ['GET','POST','PUT','DELETE'],'module'],
     "A1" :['/admin/node', ['GET','POST'],'node_adm'],
     "A2" :['/admin/contexts/' + cID(), ['GET','POST','PUT','DELETE'],'contexts_adm'],
     "A3" :['/admin/receivers/' +cID(), ['GET','POST','PUT','DELETE'],'receivers_adm'],
     "A4" :['/admin/modules/'+cID()+'/notification', ['GET','POST'],'modules_adm']
}

baseurl = "127.0.0.1:8082"


"""
In the requests, all the _GET are not reported.
I understand that may seem lazy.
err... maybe is not the best optimized code ever, having a so common
sequence of code, with just two variable changing.
"""
class requestorCollection:

    @classmethod
    def status_POST(self):

        ret = requests.submissionUpdate()
        dummy_requests.SUBMISSION_STATUS_POST(ret)
        return ret.unroll()


    @classmethod
    def finalize_POST(self):

        ret = requests.finalizeSubmission()
        dummy_requests.SUBMISSION_FINALIZE_POST(ret)
        return ret.unroll()


    @classmethod
    def tip_POST(self):

        ret = requests.tipOperations()
        dummy_requests.TIP_OPTIONS_POST(ret)
        return ret.unroll()


    @classmethod
    def comment_POST(self):

        ret = requests.sendComment()
        dummy_requests.TIP_COMMENT_POST(ret)
        return ret.unroll()


    @classmethod
    def tipfinalize_POST(self):

        ret = requests.finalizeIntegration()
        dummy_requests.TIP_FINALIZE_POST(ret)
        return ret.unroll()


    @classmethod
    def pertinence_POST(self):

        ret = requests.pertinenceVote()
        dummy_requests.TIP_PERTINENCE_VOTE(ret)
        return ret.unroll()


    @classmethod
    def module_POST(self):

        ret = requests.receiverOptions()
        dummy_requests.RECEIVER_MODULE_POST(ret)
        return ret.unroll()

    @classmethod
    def module_PUT(self):

        ret = requests.receiverOptions()
        dummy_requests.RECEIVER_MODULE_PUT(ret)
        return ret.unroll()


    @classmethod
    def module_DELETE(self):

        ret = requests.receiverOptions()
        dummy_requests.RECEIVER_MODULE_DELETE(ret)
        return ret.unroll()


    @classmethod
    def node_adm_POST(self):

        ret = requests.nodeAdminSetup()
        dummy_requests.ADMIN_NODE_POST(ret)
        return ret.unroll()


    @classmethod
    def contexts_adm_POST(self):

        ret = requests.contextConfiguration()
        dummy_requests.ADMIN_CONTEXTS_POST(ret)
        return ret.unroll()


    @classmethod
    def contexts_adm_PUT(self):

        ret = requests.contextConfiguration()
        dummy_requests.ADMIN_CONTEXTS_PUT(ret)
        return ret.unroll()


    @classmethod
    def contexts_adm_DELETE(self):

        ret = requests.contextConfiguration()
        dummy_requests.ADMIN_CONTEXTS_PUT(ret)
        return ret.unroll()


    @classmethod
    def receivers_adm_POST(self):

        ret = requests.receiverConfiguration()
        dummy_requests.ADMIN_RECEIVERS_POST(ret)
        return ret.unroll()


    @classmethod
    def receivers_adm_PUT(self):

        ret = requests.receiverConfiguration()
        dummy_requests.ADMIN_RECEIVERS_POST(ret)
        return ret.unroll()


    @classmethod
    def receivers_adm_DELETE(self):

        ret = requests.receiverConfiguration()
        dummy_requests.ADMIN_RECEIVERS_POST(ret)
        return ret.unroll()


    @classmethod
    def modules_adm_POST(self):

        ret = requests.moduleConfiguration()
        dummy_requests.ADMIN_MODULES_POST(ret)
        return ret.unroll()


class answerorCollection:

    @classmethod
    def root_GET(self):
        pass
    @classmethod
    def new_GET(self):
        pass
    @classmethod
    def status_GET(self):
        pass
    @classmethod
    def status_POST(self):
        pass
    @classmethod
    def finalize_POST(self):
        pass
    @classmethod
    def tip_GET(self):
        pass
    @classmethod
    def tip_POST(self):
        pass
    @classmethod
    def comment_POST(self):
        pass
    @classmethod
    def tipfinalize_POST(self):
        pass
    @classmethod
    def download_GET(self):
        pass
    @classmethod
    def pertinence_GET(self):
        pass
    @classmethod
    def receiver_GET(self):
        pass
    @classmethod
    def module_GET(self):
        pass
    @classmethod
    def module_POST(self):
        pass
    @classmethod
    def module_PUT(self):
        pass
    @classmethod
    def module_DELETE(self):
        pass
    @classmethod
    def node_adm_GET(self):
        pass
    @classmethod
    def node_adm_POST(self):
        pass
    @classmethod
    def contexts_adm_GET(self):
        pass
    @classmethod
    def contexts_adm_POST(self):
        pass
    @classmethod
    def contexts_adm_PUT(self):
        pass
    @classmethod
    def contexts_adm_DELETE(self):
        pass
    @classmethod
    def receivers_adm_GET(self):
        pass
    @classmethod
    def receivers_adm_POST(self):
        pass
    @classmethod
    def receivers_adm_PUT(self):
        pass
    @classmethod
    def receivers_adm_DELETE(self):
        pass
    @classmethod
    def modules_adm_GET(self):
        pass
    @classmethod
    def modules_adm_POST(self):
        pass



"""
---------------- # ---------------
"""

def do_curl(url, method, not_encoded_parm=''):
    params = urllib.urlencode(not_encoded_parm)
    headers = {
     "Content-type": "application/x-www-form-urlencoded",
     "Accept": "text/plain",
     "Accept": "application/json"
              }

    import time
    time.sleep(0.1)
    conn = httplib.HTTPConnection(baseurl)

    """
    XXX here may be modify the dict struct
    """

    if checkOpt('request'):
        print "[+] CONNECTION REQUEST:", method, baseurl, url, params, headers,"\n"

    conn.request(method, url, params, headers)

    response = conn.getresponse()

    if checkOpt('response'):
        print "[+] RESPONSE:", response.read(),"\n"

    data = response.read()
    conn.close()

    return data


def handle_selected_test(keyapi):

    url = schema[keyapi][0]
    supportedMethods = schema[keyapi][1]
    action = schema[keyapi][2]

    for method in supportedMethods:

        if method != 'GET':
            datareqf = getattr(requestorCollection, action + '_' + method)
            request = datareqf()
            output = do_curl(url, method, request)
        else:
            output = do_curl(url, method)

        dataexpectf = getattr(answerorCollection, action + '_' + method)
        # expected = dataexpectf()

        # XXX compare 'output' with 'expected'


def checkOpt(option):

    if option in sys.argv:
        return True

    return False


"""
---------------- # ---------------
"""

if __name__ != "__main__":
    print "compliment guy, you're using this test in a new way"
    raise Exception("we don't like innovation, bwahahah")

if checkOpt('verbose'):
    print "verbose is ON (imply response, request and some other details)"
if checkOpt('response'):
    print "Response verbosity printing is ON"
if checkOpt('request'):
    print "Request verbosity printing is ON"

selective = False

if len(sys.argv) >= 2:
    for x in enumerate(sys.argv):
        if x[1].find(':') != -1:
            baseurl = x[1]
            print "switching test service to:", baseurl

        if len(x[1]) == 2 and int(x[1][1]) < 7:
            selective = True
            handle_selected_test(x[1])

if not selective:
    for tests in schema.iterkeys():
        handle_selected_test(tests)

