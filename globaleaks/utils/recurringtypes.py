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
communications. It's documented in
https://github.com/globaleaks/GlobaLeaks/wiki/recurring-data-types
"""
class GLTypes:

    """
    This class is used whenever a RESTful interface need to manage
    an input element or an output element.

    The recurring elements in GLBackend, researched here:
    https://github.com/globaleaks/GLBackend/issues/14
    and documented in https://github.com/globaleaks/GlobaLeaks/wiki/recurring-data-types
    are instances based on GLTypes
    """
    def __init__(self, childname):
        """
        childname: useful for keep track of the source object, its used
            in development process
        GLTypes 
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
        This method would not be called, and is the wrapper that apply 
        regular expression in the new values.
        """

        """
        elements with "___" three underscore are created by init, and would not 
        be modified by the developer
        """
        if len(attrname) > 4 and attrname[0:2] == "___":
            raise TypeError("You can assign a new value to ___*:", attrname)

        """
        do not apply regexp enforcing for all attribute starting with "_"
        """
        if attrname[0] == "_":
            self.__dict__[attrname] = value
            return

        """
        all the other elements, need to be validated before the assignement
        """
        try:
            typecheckf = self._typetrack[attrname]['function']
        except KeyError or TypeError:
            raise AttributeError("Use 'define' method, before access to:", attrname)

        """
        If the checking function is False, and value is an instance
        of GLTypes, we're in an object assignment/replacement, then
        the object itself has been already checked.
        """
        if not typecheckf and isinstance(value, GLTypes):
            if self.__dict__.get(attrname):
                print "[++] updating", attrname, "with a new object", value.unroll()
            self.__dict__[attrname] = value
            return

        try:
            if type(self.__dict__[attrname]) == type([]):
                raise AttributeError("Can't assign to a declared array, use append")
        except KeyError:
            pass

        """
        There are a missing feature required: in an array, you can actually
        add an object with .append or .insert without being checked by the
        validation. -- XXX need to be solved.
        """

        """
        Otherwise, is a varialble, perform the check and raise an exception if
        something goes wrong with the regexp validation.
        """
        if not typecheckf(value):
            raise AttributeError("Invalid content in",attrname,"expected:",
                    typecheckname)

        if self.__dict__.get(attrname):
            print "[+] updating", attrname, "with", value
        self.__dict__[attrname] = value


    def define(self, attrname, attrtype, firstval=None):
        """
        attrname: name of the variable to be defined as JSON key
        attrtype: a valid string containing the expected type, or an instance 
            derived from GLTypes.
        firstval: a value different from the default
        'define' is the core function of GLTypes: every JSON struct need to
        be defined with is method or 'define_array'. This permit that further 
        assigment in the declared variable (accessible thru Obj.attrtype),
        shall be validated with a proper regexp
        """
        self._typetrack_initcheck(attrname)

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


    def define_array(self, attrname, attrtype, elements=0):
        """
        attrname: name of the variable to be defined as JSON key
        attrtype: a valid string or a derived class from GLTypes
        elements: number of default elements to instance in the array
        Array may contains simple or complex object.
        Arrays should have 0, 1 or N elements.
        An array instance with 0 elements, may be expanded with the classic:
        ObjectName.attrname.append() or .insert()
        """

        self._typetrack_initcheck(attrname)

        if isinstance(attrtype, GLTypes):
            self._typetrack[attrname]['function'] = False
        else:
            valf = getattr(validregexps.validatorRegExps, attrtype + "checkf")
            self._typetrack[attrname]['function'] = valf

        # define_array don't expect assignment
        valuedefault = self._getValue(attrtype, None)

        self.__dict__[attrname] = []

        for i in range(0, elements):
            self.__dict__[attrname].append( valuedefault )

    """
    Internal utility function called by define and define_array,
    it handles the value to be assigned, managing the various arguments
    and typology that may happen.
    """
    def _getValue(self, typorboth, firstassign):
        """
        typorboth: type or both (type + value, happen in the instance)
        firstassign: None or an assignment
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

    def _typetrack_initcheck(self, attrname):
        """
        do not call directly,
        shared by define() and define_array()
        """
        if self._typetrack.has_key(attrname):
            raise AttributeError("Attribute [", attrname, " already exist in the GLType")
        else:
            self._typetrack[attrname] = {}


    def _unroll_array(self, key, arrayvalue):
        """
        do not call directly this method, is used by self.unroll()
        """

        if len(arrayvalue) == 0:
            return({ key : '' })

        # in the followng case, we have 1 or more elements
        arraydumps = [ ]

        if isinstance(arrayvalue[0], GLTypes):

            for i, singleval in enumerate(arrayvalue):
                arraydumps.append( singleval.unroll() )

            return({ key : arraydumps})

        # otherwise, is not isinstance(GLTypes)
        for i, val in enumerate(arrayvalue):
            arraydumps.append( val )

        return({ key : arraydumps })


    def unroll(self):
        """
        we got four possible combination of data to be dumped in dict, and are:
        1) the common variable
        2) the referenced object, need to be called the printJSON inside of them recursively
        3) the array of (common variable|referenced object) of 0 to many items
        'unroll' return a dict walking in the child objects/arrays
        'toJSON', take a dict as argument, and return a JSON
        """
        ret = {}

        for k in self._typetrack.iterkeys():

            v = self.__dict__.get(k)

            if type(v) == type([]):
                ret.update(self._unroll_array(k, v))
            elif isinstance(v, GLTypes):
                ret.update( v.unroll() )
            else:
                ret.update({ k : v })

        return ret


    def toJSON(self, unrolled):
        """
        unrolled: a dict to be dumped in JSON format
        """
        import json
        return json.dumps(unrolled, default=dthandler)

    def aquire(self, receivedDict):
        """
        'aquire' is the method used for import and validate the
        received object. Its loop over the received dict. check if
        a key exists, and apply the validation regexp.
        """

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

        self.define_array("LanguageSupported", "string", 1)



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
        self.define("value", "string")

        # field_type need to be defined as ENUM, in the future, 
        # and would be the set of keyword supported by the 
        # client (text, textarea, checkbox, GPS coordinate)
        self.define("field_type", "string")


class moduleDataDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("mID", "moduleID")
        self.define("active", "bool")
        self.define("module_type", "moduleENUM")
        self.define("name", "string")
        self.define("module_description", "string")
        self.define("service_message", "string")

        self.define_array("admin_options", formFieldsDict(), 1 )
        self.define_array("user_options", formFieldsDict(), 1 )


class contextDescriptionDict(GLTypes):

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("cID", "contextID")
        self.define("name", "string")
        self.define("context_description", "string")
        self.define("creation_date", "time")
        self.define("update_date", "time")

        self.define_array("fields", formFieldsDict() , 1)
            # one or more, but almost one field is needed

        self.define("SelectableReceiver", "bool") 
            # update, the previous flag before was documented as
            # node-wise configuration, now is context-wise

        self.define_array("receivers", receiverDescriptionDict() )

        self.define("EscalationTreshold", "int")
            # need to be documented - along with escalation 
            # properties in Receiver element

        self.define_array("LanguageSupported", "string")
            # it's the collection of Language from 'receivers'


class commentDescriptionDict(GLTypes):
    # update: this is new

    def __init__(self):

        GLTypes.__init__(self, self.__class__.__name__)

        self.define("writtentext", "string")
        self.define("commenttype", "commentENUM")
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
        self.define_array("tiplist", tipSubIndex() )


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
        self.define_array("tip_data", formFieldsDict() )
        self.define_aray("folder", fileDict() )
        self.define_array("comment", commentDescriptionDict() )
        self.define_array("receiver_selected", receiverDescriptionDict() )




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

