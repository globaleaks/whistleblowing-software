import json
import os
import pickle

"""
Decorators applied in the implementation below.
"""
def diff(func):
    """
    Will became a function that logs in a dedicated file
    """

    def wrapper(self, v, key=func.__name__):
        values = getattr(self, "_values")

        if isinstance(v, type({})):
            keyder = v.keys()
            if values.has_key(key):
                print "update (*) in", key, "=", str(v), "was:", str(values[key])
            elif values.has_key(keyder[0]):
                print "update (`) in", keyder[0], "=", str(v), "was:", str(values[keyder[0]])
            else:
                # custom new dict
                pass
            func(self, v) if key == func.__name__ else func(self, v, key)
        elif type(values.get(key)) == type(0) and values.get(key) != 0:
            print "DIFF catch: field '"+key+"' will be", str(v), "was:", str(values.get(key))
            func(self, v) if key == func.__name__ else func(self, v, key)
        elif type(values.get(key)) == type('') and values.get(key) != '':
            print "DIFF catch: field '"+key+"' will be", str(v), "was:", str(values.get(key))
            func(self, v) if key == func.__name__ else func(self, v, key)
        else:
            # it's a new assignment
            func(self, v) if key == func.__name__ else func(self, v, key)

        # finally lanch the RestJSONwrapper.function, having
        # kept only 'readonly' operation in the _variables

    return wrapper

"""
Master class
"""
class RestJSONwrapper:

    def __init__(self):

        try:
            if not isinstance(self._values, type({}) ):
                print "Invalid usage of '_values' in " + self.__class__
        except AttributeError:
            print "Constructor " + self.__class__.__name__ + " MUST instance _values"
            quit()
        #else:
        #    print "Constructor correctly implemented"

    def fieldreview(self, ident, target_dict):

        for key, value in target_dict.items():
            if type(value) == type(' ') and value == '':
                print "[-]", ident, "missing text field in", key
            elif type(value) == type(1) and value == 0:
                print "[-]", ident, "missing int field in", key
            elif key == 'ID' or key[-2:] == 'ID':
                if not key.isalnum():
                    print "[-]", ident, "ID type not alphanumeric!"
            elif type(value) == type({}):
                # it's a dict, start recursion
                self.fieldreview(ident + '+' + key, value)
            # else, the value is set, then is fine

    def push_fields(self, bulkDict):
        # XXX - when the decorator are completed,
        #       apply here too
        self._value.update(bulkDict)


"""
Follows the implementation of RestJSONwrapper:
"""
class fileDict(RestJSONwrapper):

    def __init__(self, filename):
        self._values = dict({
            'filename' : '', 'comment' : '', 'content_type' : '',
            'size' : 0, 'date' : 0, 'metadata' : 0
        })

        self._values['filename'] = filename

        RestJSONwrapper.__init__(self)

    @diff
    def content_type(self, v):
        self._values['content_type'] = v

    @diff
    def size(self, v):
        self._values['size'] = v

    @diff
    def time(self, v):
        self._values['time'] = v

    @diff
    def comment(self, v):
        self._values['comment'] = v

    @diff
    def metadata(self, v):
        self._values['metadata'] = v

    def _fieldcomplete(self):
        if not self._values['size'] or not self.value['time']:
            statinfo = os.stat(self._values['filename'])
            self._values['size'] = statinfo.st_size
            self._values['date'] = statinfo.st_mtime

    def printJSON(self):

        # some missing values may be supply by OS
        self._fieldcomplete()

        # implemented in the master class
        self.fieldreview(self._values['filename'], self._values)

        ret = json.dumps(self._values)
        print ret, "\n"
        return ret


"""
localizationDict is a class using the storage,
"""
class localizationDict(RestJSONwrapper):

    def __init__(self, key):
        self._firstkey = key

        """
        XXX need to be specified:
        Language stay recorded in the storage or in the database ?

        from globaleaks.modules.storage import storage
        fd = storage.open('dynamic_content/localization.dat')
        innerDict = pickle.loads(fd.read())

        but actually:
        """
        self._values = pickle.load(open('localization_test.dat', 'r'))

        if not self._values.has_key(key):
            print "invalid key '"+key+"' requested"

        RestJSONwrapper.__init__(self)

    @diff
    def add_translation(self, newkey):
        """
        add_traslation pass a new:
        {'translID' : {'IT': 'ciao', 'EN': 'hello' } }
        if the key is already present, overwrite the value
        """

        if isinstance(newkey, type({}) ):
            for translID, subdict in newkey.iteritems():
                if not isinstance(subdict, type({}) ):
                    print "invalid translation block in ",translID, " = ", str(subdict)
        else:
            print "translation block expected to be a dict:", str(newkey)
            return

        self._values.update(newkey)

    @diff
    def add_language(self, newentry, translID):

        try:
            if isinstance(self._values[translID], type({}) ):
                self._values[translID].update(newentry)
        except KeyError:
            self._values.update({translID : newentry})


    def printJSON(self):

        self.fieldreview(self._firstkey, self._values)

        ret = json.dumps(self._values)
        print ret, "\n"
        return ret


class receiverDescriptionDict(RestJSONwrapper):

    def __init__(self, rID):
        self._values = ({ 
            'ID' : '', 'name' : '', 'description' : '', 
            'contact_data' : '', 'module_id' : '', 
            'module_dependent_data' : '', 
            'module_dependent_stats' : '' })

        self._values['ID'] = rID
        RestJSONwrapper.__init__(self)

    @diff
    def name(self, v):
        self._values['name'] = v

    @diff
    def description(self, v):
        self._values['description'] = v

    @diff
    def contact_data(self, v):
        self._values['contact_data'] = v

    @diff
    def module_id(self, v):
        self._values['module_id'] = v

    @diff
    def module_dependent_data(self, v):
        self._values['module_dependent_data'] = v

    @diff
    def module_dependent_stats(self, v):
        self._values['module_dependent_stats'] = v

    def set_CBP(self, v):
        """
        to be implemented - Configurable Boolean Parameter
        """

    def printJSON(self):

        self.fieldreview(self._values['ID'], self._values)

        ret = json.dumps(self._values)
        print ret, "\n"
        return ret

"""
genericDict is intended to be used 
"""
class genericDict(RestJSONwrapper):

    def __init__(self, tmpnam=''):
        self._tempnam = tmpnam
        self._values = ({})

        RestJSONwrapper.__init__(self)

    @diff
    def add_int(self, v, key):
        if type(v) != type(1):
            print "invalid argument in add_int", v, "is not an INT"
            quit()

        self._values.update({key : v})

    @diff
    def add_string(self, v, key):
        if type(v) != type('str'):
            print "invalid argument in add_string", v, "is not a string"
            quit()
        self._values.update({key : v})

    @diff
    def add_dict(self, v, key):
        if type(v) != type({}):
            print "invalid argument in add_dict", v, "is not a dict"
            quit()
        self._values.update({key : v})

    def printJSON(self):

        self.fieldreview(self._tempnam, self._values)

        ret = json.dumps(self._values)
        print ret, "\n"
        return ret

"""
formFieldDict is the field description for every FORM
"""

"""
nodePropertiesDict, actually is defined to be 
simply the "Configurable Boolean Parameters"
but need to be review in the next days -- 08/12
"""
class nodePropertiesDict(RestJSONwrapper):

    def __init__(self, CBP):
        self._values = ({})
        RestJSONwrapper.__init__(self)


"""
nodeStatisticsDict, need to be defined
"""
class nodeStatisticsDict(RestJSONwrapper):

    def __init__(self):
        print self.__class__, "not yet defined"
        pass


"""
moduleDataDict
"""
class moduleDataDict(RestJSONwrapper):

    def __init__(self, mID):
        self._values = ({ 
            'ID' : '', 'active' : None, 'module_type' : '', 
            'module_name' : '', 'description' : '', 
            'admin_options' : {}, 'user_options' : {}, 
            'service_message' : '' })

        self._values['ID'] = rID
        RestJSONwrapper.__init__(self)





"""
groupDescriptionDict
"""
#class groupDescriptionDict(RestJSONwrapper):

"""
contextDescriptionDict
"""
#class contextDescriptionDict(RestJSONwrapper):

"""
tipIndexDict
"""
#class tipIndexDict(RestJSONwrapper):

"""
tipStatistics
"""
#class tipStatistics(RestJSONwrapper):



################################################################
################################################################
# TEST

if __name__ == '__main__':


    mine1 = fileDict("/etc/passwd")
# simple update
    mine1.comment("This is an extremely sensitive document")
    mine1.metadata(1)
# diff checkINT
    mine1.content_type("text/plain")
    mine1.content_type("text/html")
    mine1.printJSON()

    mine2 = localizationDict("test1")
# simple update
    mine2.add_translation({'test2' : { 'IT' : 'it_2', 'EN' : 'en_2' }})
# verify diff in translation
    mine2.add_translation({'test2' : { 'IT' : 'due', 'EN' : 'two', 'C' : '2' }})
# add languages in both
    mine2.add_language({'FR': 'fr_1' }, 'test1')
    mine2.add_language({'FR': 'fr_2'}, 'test2')
# verify diff in language
    mine2.add_language({'FR': 'un' }, 'test1')
    mine2.add_language({'FR': 'deux' }, 'test2')
    mine2.printJSON()

    mine3 = receiverDescriptionDict('A22')
    mine3.name('vectra')
    mine3.description('well trainer driver of pack mule')
    mine3.contact_data('some kind of useful data, to be defined')
    mine3.module_id('localmailstorage')
    mine3.module_dependent_stats('32432')
    mine3.module_dependent_data('lioness@mjoll.the')
    mine3.printJSON()

    mine4 = genericDict('optionalName')
    mine4.add_int(2, 'integer')
    mine4.add_int(2, 'other_int')
    mine4.add_int(2, 'another_int')
    mine4.add_int(3, 'another_int')
    mine4.add_string('blah', 'text1')
    mine4.add_string('yadda', 'text2')
    subdict = ({'blah': [ 1,2,3], 'otherarray': [ 3,4,5 ] })
    mine4.add_dict(subdict, 'arbitrary_dict')
    mine4.add_dict({'xxx': 'yyy'}, '2nd_dict')
    mine4.add_dict({'AAA': 'BBB'}, '2nd_dict')
    mine4.printJSON()


