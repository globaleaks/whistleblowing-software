from Crypto.Random import random

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
