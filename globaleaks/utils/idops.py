from globaleaks.utils.random import random_string
from Crypto.Random import random
import re
import string

# follow the various random ID generation, with their prefix.
# the regual expression are matched in validregexps, but when
# an ID style is updated, please change also the methods below,
# implementing the appropria regexp that match the ID

# The method present here are divided in two kind:
# the random_ method: return an ID, providing randomness where request)
# the regexp_ method: return True|False, and with a regexp verify if the
#                     first argument, if fit with the appropriate format


def random_submission_id(testingmode=False):
    """
    this need to be not guessable because this secret auth the WB
    during the submission procedure.
    """
    length = 50

    if testingmode:
        return u's_'+(''.join(random.choice('A') for x in range(length)))
    else:
        return u's_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))

def regexp_submission_id(submission_id):

    outre = re.match('s_[a-zA-Z]{50,50}$', submission_id)
    return True if outre != None else False


def random_receipt_id(testingmode=False):
    """
    need to be NOT guessable
    internal settings may change the kind of the output provided (in example,
        maybe longer, or composed by words)
    the authentication of receiver maybe extended in security freature
    """
    length = 10

    if testingmode:
        return u'1234567890'
    else:
        return u''.join(random.choice('0123456789') for x in range(length))

def regexp_receipt_id(receipt):

    outre = re.match('\d{10,10}$', receipt)
    return True if outre != None else False


def random_module_id():
    """
    XXX maybe requested the:
    module_name: the name of the module, don't need to be random, but neet to be
        almost stripped of the not URL-able character that shall be present in
        the module name
    """
    length = 10
    return u'm_'+(''.join(random.choice('0123456789') for x in range(length)))

def regexp_module_id(module_id):

    outre = re.match('m_\d{10,10}$', module_id)
    return True if outre != None else False


def random_context_id():
    """
    need to be random (because not all context maybe reachable directly from the
    home page, or not all context need to be disclosed publicly), but need to be
    short, just for do not create a loooong URL
    """
    length = 20
    return u'c_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))

def regexp_context_id(context_id):

    outre = re.match('c_[a-zA-Z]{20,20}$', context_id)
    return True if outre != None else False


def random_folder_id():
    """
    need to be random
    """
    length = 20
    return u'f_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))

def regexp_folder_id(fID):

    outre = re.match('f_[a-zA-Z]{20,20}$', fID)
    return True if outre != None else False


def random_receiver_id():
    """
    maybe guessable, because is an information available to the whistleblower, and
    then every time is used as input, need to be checked in coherence, in the context.
    anyway we made it not guessable, just to avoid enumeration.
    """
    length = 20
    return u'r_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))

def regexp_receiver_id(receiver_id):

    outre = re.match('r_[a-zA-Z]{20,20}$', receiver_id)
    return True if outre != None else False


def random_tip_id():
    """
    need to be NOT guessable
    """
    length = 50
    return u't_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))

def regexp_tip_id(tID):

    outre = re.match('t_[a-zA-Z]{50,50}$', tID)
    return True if outre != None else False

