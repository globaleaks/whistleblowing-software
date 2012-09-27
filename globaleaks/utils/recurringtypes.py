# -*- coding: UTF-8
#   tip
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Contains all the logic for handling tip related operations.

from datetime import datetime
import validregexps

"""
types is a module supporting the recurring types format in JSON
communications. It's documented in: TODO


inspired by cyclone.util.ObjectDict, OD has became useless,
because of the __setattr__ and __getattr__ here extended.
"""
class GLTypes:

    """
    This class is used whenever a RESTful interface need to manage
    an input element or an output element.

    The recurring elements in GLBackend, researched here:
    https://github.com/globaleaks/GLBackend/issues/14
    and documented in TODO
    are class derived from GLTypes
    """
    def __init__(self, childname):
        """
        _typetrack would be a dict so filled:

        self._typetrack['field1']['type'] = "string"
        self._typetrack['field2']['type'] = "int"

        and when an assignmed event is called, is checked:

        self._typetrack['field1']['function'] 

        that verify if in fact the new assigned data is appropriate
        with the string regexp, and then you have:

        self.field1 (that you're SURE its a string)
        self.field2 (that you're SURE its an int)
        """
        self._typetrack = {}

        """
        this maybe useful for versioning between client/server 
        in the case a single object is updated.
        """
        self.define("___version", "string", "1")
        self.define("___typename", "string", childname)

    def __setattr__(self, attrname, value):

        """
        elements with "___" three underscore are created by init, and would not 
        be modified by the developer
        """
        if len(attrname) > 4 and attrname[0:2] == "___":
            print "temporary debug - XXX need to became an exception: you can't do that"
            return

        """
        do not apply regexp enforcing for all attribute starting with "_"
        """
        if attrname[0] == "_":
            self.__dict__[attrname] = value
            return

        """
        all the other elements, need to be verified before the assgnement
        """
        try:
            typecheckf = self._typetrack[attrname]['function']
        except KeyError or TypeError:
            raise AttributeError("Use define method before access to", attrname)

        """
        If the checking function is False,
        (imply -> attrname isinstacence of GLTypes / but check is performed again)
        there are a complete object replacement, and the sanity checks
        are performed inside of the child object.
        """
        if not typecheckf:
            if isinstance(value, GLTypes):
                print "[O] updating", attrname, "with a new object", value.unroll()
                self.__dict__[attrname] = value
                return
            else:
                raise AttributeError("unexpected condition!")

        """
        Otherwise, is a varialble, perform the check and raise an exception if
        something goes wrong with the regexp validation.
        """
        if not typecheckf(value):
            raise AttributeError("Invalid content in",attrname,"expected:",
                    typecheckname)

        print "[+] updating", attrname, "with", value
        self.__dict__[attrname] = value


    """
    Define is the core function of this object: every json field need to
    be defined along with is type. every type has a default value and 
    a validator function (included by validatoregexps.py)
    The variable value maybe initialized.
    """
    def define(self, attrname, attrtype, firstval=None):

        if self._typetrack.get(attrname) or self.__dict__.get(attrname):
            raise AttributeError("Attribute [", attrname, " already exist in the object")
        else:
            self._typetrack[attrname] = {}

        valueByType = self._getValue(attrtype, firstval)

        """
        Assign the validator regexp and the default value.

        if is found to be an istance of this class, is because
        a "recurring elements" contain other elements. 
        """
        if isinstance(attrtype, GLTypes):
            """
            In this case, we do not assign a validator function 
            because their fields has been already evaluated, and
            the attrtype is also the first assigned value
            """
            self._typetrack[attrname]['function'] = False
        else:
            valf = getattr(validregexps.validatorRegExps, attrtype + "checkf")
            self._typetrack[attrname]['function'] = valf

        self.__setattr__(attrname, valueByType)
        self._typetrack[attrname]['type'] = attrtype


    """
    Internal utility function called by define and extension,
    it handles the value to be assigned, managing the various arguments
    and typology that may happen.
    """
    def _getValue(self, typorboth, firstassign):
        """
        :typorboth = type or both (type + value, happen in the instance)
        :firstassign= None or an assignment
        """
        if isinstance(typorboth, GLTypes):

            if firstassign:
                raise TypeError("default value not expected in an object")

            return typorboth
        else:
            if firstassign:
                return firstassign

            defaultv = getattr(validregexps.defltvals, typorboth + "deflt")
            return defaultv()


    """
    Extension create an array of elements. The validation function
    remain the same
    """
    def extension(self, attrname, attrtype, firstval=None):

        if not self._typetrack.get(attrname):
            raise AttributeError("Attribute [", attrname, "] can't be extended \
                    if not yet defined")

        valueByType = self._getValue(attrtype, firstval)

        """
        Check if its already an array, if so update.
        otherwise, make a temporary backup and create it
        """
        if type(self.__dict__.get(attrname)) == type([]):
            self.__dict__[attrname].append(valueByType)
        else:
            backup = self.__dict__[attrname]
            self.__dict__[attrname] = [ backup, valueByType ]

    """
    we got four possible combination of data to be dumped by JSON format,
    and are:
    1) the common variable
    2) the referenced object, need to be called the printJSON inside of them recursively
    3) the array of common variable
    4) the array of referenced object.

    follow the three functions moving in the tree:

    'debug' function (print to stdout)
    'unroll' return a dict walking in the child objects/arrays
    'toJSON', take a dict as argument, and return a JSON

    """
    def debug(self):

        for k in self._typetrack.iterkeys():
            v = self.__dict__.get(k)
            if isinstance(v, GLTypes):
                print "entering recursion in", k
                v.debug()
            elif type(v) == type([]) and not isinstance(v[0], GLTypes):
                print "array of ",len(v), "in ", k
                for i, val in enumerate(v):
                    print "  ",val
            elif type(v) == type([]) and isinstance(v[0], GLTypes):
                print "array of an instance ",len(v), "in ", k
                for i, val in enumerate(v):
                    print "recursion #", i
                    val.debug()
            else:
                print "dumping of", k, " = ", v

    def unroll(self):
        ret = {}
        for k in self._typetrack.iterkeys():
            v = self.__dict__.get(k)
            if isinstance(v, GLTypes):
                ret.update( v.unroll() )
            elif type(v) == type([]) and not isinstance(v[0], GLTypes):
                ret.update({ k : v })
            elif type(v) == type([]) and isinstance(v[0], GLTypes):
                objs = []
                for i, val in enumerate(v):
                    objs.append( val.unroll() )
                ret.update({ k : objs })
            else:
                ret.update({ k : v })

        return ret

    def toJSON(self, unrolled):
        import json
        return json.dumps(unrolled, default=dthandler)

    """
    'aquire' is the method used for import and validate the
    received object. Its loop over the received dict, for 
    every key check if in fact exists, and 
    """
    """
    ACTUALLY IS BUGGED - NEED TO BE FIXED IN HANDLING SUB DICT
    AND ARRAYS (that are optionals: can be #0 element, can be #N,
    can be #1)
    """
    def aquire(self, receivedDict):

        for k in receivedDict.iterkeys():

            print "next iter ",k, 
            try:
                localAttrib = getattr(self, k)
            except AttributeError:
                raise AttributeError("importing malformed data", k, "in", dir(self) )

            v = receivedDict.get(k)
            print "-- processing", type(v), " in ", k, " = ", v

            if type(v) == type([]):
                print "[-] handle an array"
            elif type(v) == type({}):
                print "[--] handle a dict"
            else:
                print "[++] aquiring ", v," in localAttr",str(k), type(v)
                localAttrib = v


"""
Object derivation from GLTypes, they are documented in: TODO
"""

class fileDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("filename", "string")
        self.define("file_description", "string")
        self.define("size", "int")
        self.define("content_type", "string")
        self.define("date", "time")
        self.define("cleaned_meta_data", "bool")


class receiverDescriptionDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("rID", "receiverID")
        self.define("CanDeleteSubmission", "bool")
        self.define("CanPostponeExpiration", "bool")
        self.define("CanConfigureNotification", "bool")
        self.define("CanConfigureDelivery", "bool")

            # -----------------------------------------
        self.define("CanTriggerEscalation", "bool") 
        self.define("ReceiverLevel", "int") 
            # remind: both of them need to be specified

        self.define("receiver_name", "string")
        self.define("receiver_description", "string")
        self.define("receiver_tags", "string")
            # verify - is it specified ?
        self.define("creation_date", "time")
        self.define("last_update_date", "time") 
            # update the name

        self.define("LanguageSupported", "string")
        self.extension("LanguageSupported", "string")
        self.extension("LanguageSupported", "string")
        self.extension("LanguageSupported", "string")
            # update - before was in the group element



"""
Gradually this options has been shrinked because:
    1) threat model need to be completed
    2) some of them has been moved in the Contexts
    3) CBP are aimed in leakdirectory integration
"""
class nodePropertiesDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("AnonymousSubmissionOnly", "bool")


"""
This containers need to be defined, IMHO would be an aggregate
of information collected about the latest X-hours of the node
and so far
"""
class adminStatisticsDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("hours_interval", "int")
        self.define("download_number", "int")
        self.define("receiver_accesses", "int")
        self.define("submission_received", "int")


"""
The following container is used for the public statistic,
collected by site that perform uptime and/or measurement, 
or readed by users.
Need to be defined, depends what's is considered to be 
harmless for node life, and what's can be easily collected
"""
class publicStatisticsDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("active_contexts", "int")
        self.define("active_receivers", "int")
        self.define("uptime_days", "int")


class formFieldsDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("presentation_order", "int")
        self.define("name", "string")
        self.define("required", "bool")
        self.define("field_description", "string")


class moduleDataDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("mID", "moduleID")
        self.define("active", "bool")
        self.define("type", "moduleENUM")
        self.define("name", "string")
        self.define("module_description", "string")
        self.define("service_message", "string")

        self.define("admin_options", formFieldsDict() )
        self.extension("admin_options", formFieldsDict() )
        self.extension("admin_options", formFieldsDict() )
        self.extension("admin_options", formFieldsDict() )

        self.define("user_options", formFieldsDict() )
        self.extension("user_options", formFieldsDict() )
        self.extension("user_options", formFieldsDict() )


class contextDescriptionDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("cID", "contextID")
        self.define("name", "string")
        self.define("context_description", "string")
        self.define("creation_date", "time")
        self.define("update_date", "time")

        self.define("fields", formFieldsDict() )
        self.extension("fields", formFieldsDict() )
        self.extension("fields", formFieldsDict() )
        self.extension("fields", formFieldsDict() )

        self.define("SelectableReceiver", "bool") 
            # update, the previous flag before was documented as
            # node-wise configuration, now is context-wise

        self.define("receivers", receiverDescriptionDict() )
        self.extension("receivers", receiverDescriptionDict() )
        self.extension("receivers", receiverDescriptionDict() )
        self.extension("receivers", receiverDescriptionDict() )
            # in the documentation there are the group concept
            # actually removed

        self.define("EscalationTreshoold", "int")
            # need to be documented - along with escalation 
            # properties in Receiver element

        self.define("LanguageSupported", "string")
        self.extension("LanguageSupported", "string")
        self.extension("LanguageSupported", "string")
        self.extension("LanguageSupported", "string")
        self.extension("LanguageSupported", "string")
            # need to be updated, before was in the group


class commentDescriptionDict(GLTypes):
    # update: this is new

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("writtentext", "string")
        self.define("type", "commentENUM")
        self.define("author", "string")
        self.define("date", "time")



"""
Remind, this Tip access is different for every receiver,
Remind: this object is the LIST OF ACTIVE TIP, does not
cover the content.
"""
class tipIndexDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("cID", "contextID")
        self.define("tiplist", tipSubIndex() )
        self.extension("tiplist", tipSubIndex() )
        self.extension("tiplist", tipSubIndex() )


class tipSubIndex(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("tID", "tipID")
        self.define("tip_title", "string")

        self.define("notification_adopted", "string")
        self.define("delivery_adopted", "string")

        self.define("download_limit", "int")
        self.define("download_performed", "int")
        self.define("access_limit", "int")
        self.define("access_performed", "int")

        self.define("expiration_date", "time")
        self.define("creation_date", "time")
        self.define("last_update_date", "time")

        self.define("comment_number", "int")
        self.define("folder_number", "int")
        self.define("overall_pertinence", "int")


class tipDetailsDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        """
        This element contain mostly of the descriptive information
        of the Tip
        """
        self.define("tip", tipSubIndex() )

        """
        What's follow are the details Tip dependent
        """
        self.define("tip_data", formFieldsDict() )
        self.extension("tip_data", formFieldsDict() )
        self.extension("tip_data", formFieldsDict() )

        self.define("folder", fileDict() )
        self.extension("folder", fileDict() )
        self.extension("folder", fileDict() )

        self.define("comment", commentDescriptionDict() )
        self.extension("comment", commentDescriptionDict() )
        self.extension("comment", commentDescriptionDict() )
        self.extension("comment", commentDescriptionDict() )

        self.define("receiver_selected", receiverDescriptionDict() )
        self.extension("receiver_selected", receiverDescriptionDict() )
        self.extension("receiver_selected", receiverDescriptionDict() )
        self.extension("receiver_selected", receiverDescriptionDict() )




"""
This object would be implemented when localization would be solved
as issue: https://github.com/globaleaks/GLBackend/issues/18
"""
class localizationDict(GLTypes):
    pass


"""
*************************************
temporary test, a dict to be accepted
*************************************
"""

def do_aquire():
    import datetime

    fileDict().aquire(fileDict().unroll())
    tipSubIndex().aquire(tipSubIndex().unroll())
    receiverDescriptionDict().aquire(receiverDescriptionDict().unroll())
    contextDescriptionDict().aquire(contextDescriptionDict().unroll())
    formFieldsDict().aquire(formFieldsDict().unroll())
    tipDetailsDict().aquire(tipDetailsDict().unroll())

if __name__ == '__main__':
    do_aquire()

