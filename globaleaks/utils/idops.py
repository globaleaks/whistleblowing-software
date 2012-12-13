# -*- coding: UTF-8
#   idops
#   *****
#
# follow the various random ID generation, being a string,
# they taken the name of GUS (GlobaLeaks Unique String) 
# and the ID is used only for the incremental integer identifier
#
# The regular expression matching those formats, are implemented
# in globaleaks/rest/base.py
#
# All the GUS string had byte in 
# the start, identify in visual way what's is the roles of the GUS, 
# like "s_" is a submnission_gus, "t_" a tip_gus
#
# TODO
# The regexp maybe uniformed, using the same of submission/tip instead
# select some gus with a number only, or a shorter list.


from Crypto.Random import random
import string


def random_submission_gus(testingmode=False):
    """
    this need to be not guessable because this secret auth the WB
    during the submission procedure.
    """
    length = 50

    if testingmode:
        return u's_'+(''.join(random.choice('A') for x in range(length)))
    else:
        return u's_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))

def random_receipt_gus(testingmode=False):
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

def random_plugin_gus():
    length = 10
    return u'p_'+(''.join(random.choice('0123456789') for x in range(length)))

def random_context_gus():
    """
    need to be random (because not all context maybe reachable directly from the
    home page, or not all context need to be disclosed publicly), but need to be
    short, just for do not create a loooong URL
    """
    length = 20
    return u'c_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))

def random_folder_gus():
    """
    need to be random
    XXX this has been changed to starting d_ for directory.
    """
    length = 20
    return u'd_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))

def random_file_gus():
    """
    need to be random
    XXX file is now starting with f_ and is supposed to be random
    """
    length = 30
    return u'f_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))

def random_receiver_gus():
    """
    maybe guessable, because is an information available to the whistleblower, and
    then every time is used as input, need to be checked in coherence, in the context.
    anyway we made it not guessable, just to avoid enumeration.
    """
    length = 20
    return u'r_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))

def random_tip_gus():
    """
    need to be NOT guessable
    """
    length = 50
    return u't_'+(''.join(random.choice(string.ascii_letters) for x in range(length)))
