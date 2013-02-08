# -*- coding: UTF-8
#   random
#   ******
#
# Interface for generate random string using a safe random number generator.

from Crypto.Random import random
from Crypto.Hash import SHA256
from twisted.internet import fdesc

def random_string(length, type):
    """
    Generates a random string of specified length and type.

    :length: the length of the random string
    :type: needs to be passed as comma separated ranges or values,
           ex. "a-z,A-Z,0-9".
    """
    def parse(type):
        choice_set = ''
        parsed = type.split(',')
        for item in parsed:
            chars = item.split('-')
            if len(chars) > 1:
                for chars in range(ord(chars[0]), ord(chars[1])):
                    choice_set += chr(chars)
            else:
                choice_set += chars[0]
        return choice_set

    choice_set = parse(type)
    res = ''.join(random.choice(choice_set)
                  for x in range(0, length))
    return res


def get_file_checksum(filepath):

    sha = SHA256.new()

    chunk_size = 8192

    with open(filepath, 'rb') as fd:

        fdesc.setNonBlocking(fd.fileno())
        while True:
            chunk = fd.read(chunk_size)
            if len(chunk) == 0:
                break
            sha.update(chunk)

    return sha.hexdigest()

def get_string_checksum(rawstring):

    return SHA256.new().update(rawstring)

