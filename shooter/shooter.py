#!/usr/bin/python

import string
import sys, os
import subprocess
import tempfile
import json

cwd = '/'.join(__file__.split('/')[:-1])
sys.path.insert(0, os.path.join(cwd, '../'))

# Need to be updated, this table and the options usable in shooter.py
# TODO - to be fixed with generate_docs.py
# Remind: this was the format
URTA = {

    'U1_GET':'GET_/node',
    'U2_POST':'POST_/submission',
    'U3_PUT':'PUT_/submission/@SID@',
    'U3_DELETE':'DELETE_/submission/@SID@',
    'U3_GET':'GET_/submission/@SID@',
    'U4_POST':'POST_/submission/@SID@/file',
    'U4_DELETE':'DELETE_/submission/@SID@/file',
    'U4_GET':'GET_/submission/@SID@/file',
    'U5_GET':'GET_/statistics',
    'U6_GET':'GET_/contexts',
    'U7_GET':'GET_/receivers',

    'T1_PUT':'PUT_/tip/@TIP@',
    'T1_DELETE':'DELETE_/tip/@TIP@',
    'T1_GET':'GET_/tip/@TIP@',
    'T2_POST':'POST_/tip/@TIP@/comments',
    'T2_GET':'GET_/tip/@TIP@/comments',
    'T3_GET':'GET_/tip/@TIP@/receivers',

    'A1_GET':'GET_/admin/node',
    'A1_PUT':'PUT_/admin/node',
    'A2_GET':'GET_/admin/context',
    'A2_POST':'POST_/admin/context',
    'A3_GET':'GET_/admin/context/@CID@',
    'A3_PUT':'PUT_/admin/context/@CID@',
    'A3_DELETE':'DELETE_/admin/context/@CID@',
    'A4_GET':'GET_/admin/receiver',
    'A4_POST':'POST_/admin/receiver',
    'A5_GET':'GET_/admin/receiver/@RID@',
    'A5_PUT':'PUT_/admin/receiver/@RID@',
    'A5_DELETE':'DELETE_/admin/receiver/@RID@',
    'A6_GET':'GET_/admin/plugin',
    'A7_GET':'GET_/admin/profile',
    'A7_POST':'POST_/admin/profile',
    'A8_GET':'GET_/admin/profile/@PID@',
    'A8_PUT':'PUT_/admin/profile/@PID@',
    'A8_DELETE':'DELETE_/admin/profile/@PID@',
    'A9_GET':'GET_/admin/statistics/',

    'D1_GET':'GET_/debug/overview/@DUMP@',
    'D2_DELETE':'DELETE_/debug/tasks/@TASK@',
    'D2_GET':'GET_/debug/tasks/@TASK@',

    'R2_GET':'GET_/receiver/@TIP@/profile',
    'R3_GET':'GET_/receiver/@TIP@/profileconf',
    'R3_POST':'POST_/receiver/@TIP@/profileconf',
    'R4_GET':'GET_/receiver/@TIP@/profileconf/@CFGID@',
    'R4_PUT':'PUT_/receiver/@TIP@/profileconf/@CFGID@',
    'R4_DELETE':'DELETE_/receiver/@TIP@/profileconf/@CFGID@'
}

baseurl = "http://127.0.0.1:8082"
output_handling = False

def do_httpie(method, url, request_list):
    """
    @param url:
    @param method:
    @param request_list: should not be present, is the value in HTTPie format. ref search_jsonfile
    @return: No return, the code execution end here.
    """
    (tstderr, errfname) = tempfile.mkstemp(suffix="_shootErr")

    if checkOpt('verbose'):
        tstdout = sys.stdout
        outfname = None
    else:
        (tstdout, outfname) = tempfile.mkstemp(suffix="_shootOut")

    tstderr = sys.stderr
    defurl = baseurl + url

    command_array = ["http", "--check-status", method, defurl ]

    if request_list is not None:
        for request_element in request_list:
            command_array.append(request_element)

    if checkOpt('verbose'):
        command_array.append('--verbose')

    try:
        subprocess.check_call(command_array, stderr=tstderr, stdout=tstdout)
    except subprocess.CalledProcessError:
        print "invalid execution of httpie!, command line:", sys.argv
        print "error file:", errfname
        quit(1)
    except OSError:
        print "You need HTTPie installed. Check 'Requirement' section in README.md"
        quit(1)

    if outfname == None:
        # verbose option, do not permit output parsing,
        # good exit code here
        quit(0)

    os.close(tstdout)
    with open(outfname, 'r') as outfstream:
        readed = outfstream.read()

    if len(readed) > 5 and output_handling == True:
        # If we're received data, mean that 'verbose' option was not present
        if outputOptionsApply(json.loads(readed)) == False:
            os.unlink(outfname)
            os.unlink(errfname)
            print "pattern searched not found in the output"
            quit(1)

    os.unlink(outfname)
    os.unlink(errfname)
    quit(0)


def checkOpt(option):

    if option in sys.argv:
        return True

def getOpt(seekd):

    if seekd in sys.argv:

        try:
            retarg = sys.argv[sys.argv.index(seekd) + 1]
        except IndexError:
            print "unable to get [", seekd,"] required parameter"
            quit(1)

        return retarg

    return None

def fix_varline(inputline):

    returnline = inputline
    for var,argopt in { 
            '@TIP@': 'tip', # Tip GUS
            '@CID@': 'cid', # Context GUS
            '@SID@': 'sid', # Session GUS
            '@RID@': 'rid', # Receiver GUS
            '@RAW@': 'raw', # RAW JSON string
            '@CFGID@': 'cfgid', # Receiver Config ID
            '@TASK@': 'task', # task scheduled type, or table shortnames
            '@DUMP@': 'dump', # task scheduled type, or table shortnames
            '@PID@' : 'pid', # Profile GUS (plugin)
            '@CN@' : 'cn'   # Configuration Number (numeric ID)
                }.iteritems():

        if returnline.find(var) > 0:

            # is expected in command line: tip,rid,cid,sid,dump,task or raw
            user_parm = getOpt(argopt)

            if user_parm is None:
                print "processed line has a variable(", inputline, "), you need to specify", argopt
                quit(1)

            linesplit = returnline.split(var)

            if user_parm == "None":
                returnline = (linesplit[0] + linesplit[1])
            else:
                returnline = (linesplit[0] + user_parm + linesplit[1])

    # special directive @RANDOM@
    special = '@RANDOM@'
    if returnline.find(special) > 0:

        linesplit = returnline.split(special)
        return (linesplit[0] + str(random.randint(1,100000)) + linesplit[1])

    return returnline

def getMethIf(argv_index):
    if len(sys.argv) > argv_index:
        if sys.argv[argv_index].upper() in ['GET', 'POST', 'DELETE', 'PUT' ]:
            return sys.argv[argv_index].upper()

    return None

def spelunking_into_URTA():

    meth = getMethIf(2)
    if not meth:
        print "assumed method: GET"
        meth = 'GET'

    assembled_key = sys.argv[1] + "_" + meth

    if URTA.has_key(assembled_key):
        aggregate = URTA[assembled_key]
    else:
        print "The U|R|T|A code + method requested is invalid", assembled_key
        quit(1)

    # (url, meth, aggregate)
    return (aggregate.split("_")[1], meth, aggregate)



def search_jsonfile(searched_rest):

    fileconv = string.replace(string.replace(searched_rest, '@', ''), '/', '_')

    variation = getOpt('variation')

    if variation:
        fname = 'jsonfiles/' + fileconv + '.' + variation
    else:
        fname = 'jsonfiles/' + fileconv

    if os.access(fname, os.R_OK):
        retlist = [] # it's a list because every line is a different parm in httpie
        with open(fname, 'r') as f:
            while True:

                line = string.strip(f.readline(), "\n")

                if len(line) <= 1:
                    return retlist

                if line[0] == '#':
                    continue

                expanded_line = fix_varline(line)
                retlist.append(expanded_line)
    else:
        print "input JSON file is missing, searched:", fname
        quit(1)


def outputOptionsApply(theDict):

    retval = False

    if type(theDict) != type({}):
        return retval 

    for uarg in sys.argv:
        if uarg.startswith('print-'):
            # more than one print- option can be present
            choosen = uarg[6:]

            if theDict.has_key(choosen):
                print theDict[choosen]
                retval = True

            for key, value in theDict.iteritems():
                # it's a list ?
                if type(value) == type([]):
                    for element in theDict.get(key):
                        retval |= outputOptionsApply(element)

                # it's a dict ?
                if type(value) == type({}):
                    retval |= outputOptionsApply(value)
    return retval


if __name__ == '__main__':

    import random
    random.seed(os.getpid())

    if len(sys.argv) < 2:
        print sys.argv[0], "[portion of REST]|URTA code", "<method>",
        "<sid>|<cid>|<tip>|<rid>|<raw>|<task>|<dump>|<pid>|<cn>|<cfgid>"
        quit(1)

    if sys.argv[1] == 'help':
        for key, value in URTA.iteritems():
            (urta, method) = key.split("_")
            (dirt, path) = value.split("_")
            print "%s\t%s\t%s" % (urta, method, path)
        print "D1 dump = [receivers|itip|rtip|wtip|context|submission|file|all]"
        print "D2 task = [statistics|welcome|tip|delivery|notification|cleaning|digest]"
        quit(0)

    for uarg in sys.argv:
        if uarg.startswith('print-'):
            output_handling = True

    # handle 'shooter.py U1' and 'shooter.py U1 POST'
    if len(sys.argv[1]) != 2:
        print "expected a code like (U|R|T|A) with a number"
        quit(1)

    (url, meth, aggregate) = spelunking_into_URTA()

    if meth != 'GET' and meth != 'DELETE':
        request_list = search_jsonfile(aggregate)
    else:
        request_list = None

    url_fixed = fix_varline(url)
    do_httpie(meth, url_fixed, request_list)
