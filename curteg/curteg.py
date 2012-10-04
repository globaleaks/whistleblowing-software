import httplib, json
import sys, os, time

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
Request schema,
linking the identificative synthesis, the URL, the method
"""
schema = {
     "U1" :['/node', ['GET'],'root'],
     "U2" :['/submission', ['GET'],'new'],
     "U3" :['/submission/'+sID()+'/status', {
          'GET' : None,
          'POST' : [ requests.submissionUpdate, dummy_requests.SUBMISSION_STATUS_POST ] 
          } ],
     # "U5" :['/submission/'+sID()+'/files', ['GET','POST','PUT','DELETE']],
     "U4" :['/submission/'+sID()+'/finalize', {
         'POST': [ requests.finalizeSubmission, dummy_requests.SUBMISSION_FINALIZE_POST ]
         } ],
     "T1" :['/tip/', {
         'GET' : None,
         'POST' : [ requests.tipOperations, dummy_requests.TIP_OPTIONS_POST ]
         } ],
     "T2" :['/tip/'+tID()+'/comment', {
         'POST' : [ requests.sendComment, dummy_requests.TIP_COMMENT_POST ]
         } ],
     # "T3" :['/tip/'+tID()+'/files', ['GET','POST','PUT','DELETE']],
     "T4" :['/tip/'+tID()+'/finalize', {
         'POST' : [ requests.finalizeIntegration, dummy_requests.TIP_FINALIZE_POST ]
         } ],
     "T5" :['/tip/'+tID()+'/download', {
         'GET' : None
         } ],
     "T6" :['/tip/'+tID()+'/pertinence', { 
         'POST' : [ requests.pertinenceVote, dummy_requests.TIP_PERTINENCE_POST ]
         } ],
     "R1" :['/receiver/' + tID(), {
         'GET' : None,
         } ],
     "R2" :['/receiver/' + tID() +'/notification', {
         'GET' : None,
         'POST' : [ requests.receiverOptions, dummy_requests.RECEIVER_MODULE_POST ],
         'PUT' : [ requests.receiverOptions, dummy_requests.RECEIVER_MODULE_PUT ],
         'DELETE' : [ requests.receiverOptions, dummy_requests.RECEIVER_MODULE_DELETE ]
         } ],
     "A1" :['/admin/node', {
         'GET' : None,
         'POST' : [ requests.nodeAdminSetup, dummy_requests.ADMIN_NODE_POST ]
         } ],
     "A2" :['/admin/contexts/' + cID(), {
         'GET' : None,
         'POST' : [ requests.contextConfiguration, dummy_requests.ADMIN_CONTEXTS_POST ],
         'PUT' : [ requests.contextConfiguration, dummy_requests.ADMIN_CONTEXTS_PUT ],
         'DELETE' : [ requests.contextConfiguration, dummy_requests.ADMIN_CONTEXTS_DELETE ]
         } ],
     "A3" :['/admin/receivers/' +cID(), {
         'GET' : None,
         'POST' : [ requests.receiverConfiguration, dummy_requests.ADMIN_RECEIVERS_POST ],
         'PUT' : [ requests.receiverConfiguration(), dummy_requests.ADMIN_RECEIVERS_PUT ],
         'DELETE' : [ requests.receiverConfiguration, dummy_requests.ADMIN_RECEIVERS_DELETE ]
         } ],
     "A4" :['/admin/modules/'+cID()+'/notification', {
         'GET' : None,
         'POST' : [ requests.moduleConfiguration, dummy_requests.ADMIN_MODULES_POST ]
         } ]
}

baseurl = "127.0.0.1:8082"


"""
29 elements, possible answerd that would be checked in integrity 
             to understand if the backend hasanswered well
"""
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

    headers = {'Content-Type': 'application/json-rpc; charset=utf-8'}
    params = json.dumps(not_encoded_parm, ensure_ascii=False)
    params.encode('utf-8')

    time.sleep(0.1)
    conn = httplib.HTTPConnection(baseurl)

    """
    XXX here may be modify the dict struct, if option request
    """

    if checkOpt('request'):
        print "[+] CONNECTION REQUEST:", method, baseurl, url, not_encoded_parm, headers,"\n"

    conn.request(method, url, params, headers)

    response = conn.getresponse()

    if checkOpt('response'):
        print "[+] RESPONSE:", response.read(),"\n"

    data = response.read()
    conn.close()

    return data


"""
['/submission/s_LCjNrPCGDqeMbQaIUbNbKUPtrrDuArvkEMlSAUwduQgJewpIfR/status', {'POST': [<class
globaleaks.rest.requests.submissionUpdate at 0x224a0b8>, <function SUBMISSION_STATUS_POST at
0x2252050>], 'GET': None}]
"""
def handle_selected_test(keyapi):

    url = schema[keyapi][0]
    methodsAndFunctions = schema[keyapi][1]

    requestedMethods = []
    for meth in [ 'GET', 'POST', 'PUT', 'DELETE' ]:
        if checkOpt(meth):
            requestedMethods.append(meth)

    for method in methodsAndFunctions.iterkeys():
        if len(requestedMethods) > 0 and not (method in requestedMethods):
            print "skipping", url, method
            continue

        #___ answerGLT = methodsAndFunctions.get(method)[2]()

        # GET has not a request, then
        if method == 'GET':
            output = do_curl(url, method)
            #___ compare_output(output, answerGLT)
            continue

        # request generation: call globaleaks.rest.requests
        requestGLT = methodsAndFunctions.get(method)[0]()
        # request filling: call globaleaks.utils.dummy.dummy_requests
        methodsAndFunctions.get(method)[1](requestGLT)
        # requestGLT need to be .unroll() for be a dict
        request = requestGLT.unroll()

        # If the option request modification of the request, here has to appen

        # XXX

        output = do_curl(url, method, request)
        #___ compare_output(output, answerGLT)


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
    for opt in enumerate(sys.argv):
        if opt[1].find(':') != -1:
            baseurl = x[1]
            print "switching test service to:", baseurl

        if len(opt[1]) == 2 and int(opt[1][1]) < 9:
            selective = True
            handle_selected_test(opt[1])

if not selective:
    for tests in schema.iterkeys():
        handle_selected_test(tests)

