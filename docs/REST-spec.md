# Summary

This is a breif summary of the REST API specification.

## Public API

A syntax has been defined to adress the single REST:

Public (P)
Receiver (R)
Tip (T)
Admin (A)

Followed by an incremental number, this would make easy keep track of which REST has been implemented and, if updated, can be easily address the changed interfaces.

### API accessible at all users

P1 `/node/`

Returns information on the GlobaLeaks node. This includes submission paramters and how information should be presented by the client side application.

P2 `/submission`

This creates an empty submission and returns the Id to be used when referencing it as a whistleblower.
Id is a random 64bit integer (GET)

P3 `/submission/<submission_id>/status`

Returns the currently submitted fields and material filenames and size, this is the only interface giving back the complete submission status (GET, POST)
Awaits for the group matrix selection, awaits for the fields.

P4 `/submission/<submission_id>/finalize`

Completes the submission in progress, **give to the server the receipt secret** and confirm the receipt (or answer with a part of them). settings dependent.  (POST)

P5 `/submission/<submission_id>/files`

upload a file to the selected submission_id (REST depends from JQueryFileUpload integration, probabily GET, POST, DELETE, PUT)

### API shared between WhistleBlowers and Receiver (require auth)

T1 `/tip/<string auth t_id>`

Returns the content of the submission with the specified Id.
Inside of the request headers, if supported, the password for accessing the tip can be passed.
This returns a session token that is then used for all future requests to be authenticated.
Supports GET (all status data), POST (comment and pertinence)

T2 `/tip/<uniq_Tip_$ID>/comment`

Both WB and Receiver can write a comment in a Tip (POST only)

### Tip subsection API (WhistleBlower only)

T3 `/tip/<uniq_Tip_$ID>/files`

Add a new folder files in the associated submission, (update the Tip for all the
receiver, in regards of the modules supports)
The material is published when 'finalized'.
(GET, POST)

T4 `/tip/<string t_id>/finalize`

Used to add a description in the uploaded files.
This action make the new uploaded data available for download.
If this action is missed, the material can be published after a timeout expiring
at midnight (MAY BE REVIEWED) (POST only)

### Tip subsection (API Receivers only)

T5 `/tip/<string t_id>/download`

This interface can be disabled by delivery configuration.

used to download the material from the
submission. if a download limit has been configured, can be requested
only if relative download count is < max_downloads (POST only).

Paramters inside the POST specify which Material Set and the requested
mode (compressed, encrypted)

T6 `/tip/<string t_id>/pertinence`

This interface can be disabled by administrative settings.
express a pertinence value (-1 or +1, True/False) (POST only)

## Receiver API

R1 `/receiver/<string t_id>/overview`

Brief summary of all related Tip, and brief view of personal settings
customizable by the receiver.

R2 `/receiver/<string t_id>/<string module_name>`

Flexible interface handled by every module configurabile by receiver

## Admin API

A1 `/admin/node/`

For configuring the *public* details of the node, the private details are
set in the specific resources

A2 `/admin/contexts/`

List, delete, update or create contexts (GET, POST), obtain all the
context_$ID, properties, description.

A3 `/admin/groups/<context_$ID>/`

Having the context_$ID, list, delete, update or create groups of receiver,
every group has an extension module configured to manage correctly the
kind of receiver present.

A4 `/admin/receivers/<group_$ID>/`

Having the group_$ID of a certain group, the admin can perform
CURD operation over the group. Adding receiver, change properties,
delete and update.

A5 `/admin/modules/<string module_type>/`

as defined in [issue #15](https://github.com/globaleaks/GLBackend/issues/15), there
are various flexible section of GLBackend configurable and choosable by the
administrator. Here would be listed, selected and configured. Every module
is a python file present in the running code, update the modules list would require
a remote access.

# Synthesis

P1 `/node/`

P2 `/submission`
P3 `/submission/<submission_$ID>/status`
P4 `/submission/<submission_$ID>/finalize`
P5 `/submission/<submission_$ID>files`

R1 `/receiver/<string t_id>/overview`
R2 `/receiver/<string t_id>/<string module_name>`

A1 `/admin/node/`
A2 `/admin/contexts/`
A3 `/admin/group/<context_$ID>/`
A4 `/admin/receivers/<group_$ID>/`
A5 `/admin/modules/<string module_type>/`

_Note: all the Tip interfaces depends on Tip implementation, the presented interface are the default Tip_

T1 `/tip/<uniq_Tip_$ID>`
T2 `/tip/<uniq_Tip_$ID>/comment`
T3 `/tip/<uniq_Tip_$ID>/files`
T4 `/tip/<uniq_Tip_$ID>/finalize`
T5 `/tip/<uniq_Tip_$ID>/download`
T6 `/tip/<uniq_Tip_$ID>/pertinence`

# Description syntax adopted in this document

In the REST specification, the JSON element are express in python cohernt embeddable list and tuple.
When this format is used:

     'key': [
               { 'label1': 'value-one', 'label2' : 'SpecialType-two' },
               { }
            ]

Mean that key address an array of elements. The format of the element is reported only once, and the
possible presence of other elements is represented by " { } " before the array closure.

# Data Object involved

The simplex involved datatype used in this REST specification are:

    'Int', a numeric positive value
    'string'
    'Bool', True|False

    { 'key' : 'value' }, a tuple
    [ 'elem1', 'elem2', 'elem3' ] an array of elements

Exists also some complex datatype, they are written in this document with the "$" in front
of the datatype-name, the list and the detailed meaning would be found in:
[issue #14](https://github.com/globaleaks/GLBackend/issues/14), this is the reference.

  * **ID**: Identified, is an unique value amount the same kind of data, and would be
    and integer or a string user choosen. The property of the Id is to be unique.

  * **fileDict**: file descriptor element, every file (uploaded or available in download) is
    represented with this dict:

        {   'filename': 'string',
            'comment': 'string',
            'size': 'Int',
            'content_type': 'string',
            'date': 'Time',
            'CleanedMetaData': 'int'
        }

    CleanedMetaData maybe expanded, actually are 0 (unknow) 1 (cleaned) 2 (not cleaned),
    and is declared by the user.

  * **localizationDict**: the Local Dict is an object used to store localized texts, in example:

        {   'IT' : 'Io mi chiamo Mario.',
            'EN' : 'Is a me, Mario!!1!',
            'FR' : "je m'appelle Marìò, pppffff"
        }

  * **receiverDescriptionDict**, series of tuple with boolean values, expressing the permissions given
    to a receiver, and series of descriptive data for the single receiver.

    **Those properties list need to be reviewed with the community and the legal team**

        {   'ReceiverID': '$ID',
            'CanDeleteSubmission': 'Bool',
            'CanPostponeExpiration': 'Bool',
            'CanConfigureNotification': 'Bool',
            'CanConfigureDelivery': 'Bool',
            'receiver_name': 'string',
            'receiver_description': 'string',
            'receiver_tags': 'string',
            'contact_data': 'string',
            'creation_date': 'Time',
            'update_date': 'Time'
            'module_id': $ID,
            'module_dependent_data': '$formFieldsDict',
            'module_dependent_stats': 'Array'
        }

    This element may contain sensitive data: is exposed only in administrative interfaces
    and personal management interface (/receivers/...)


  * **nodePropertiesDict**, series of tuple with boolean value, expressing the property
    configured in the node (those property would be in the future linked with the
    privacy policy of the node, and the security capabilities enforced in the node)

        {   'AnonymousSubmissionOnly': 'Bool',
            'AdminAreReceivers': 'Bool',
            'NodeProvideDocsPublication': 'Bool',
            'FixedCorpusOfReceiver': 'Bool',
            'ReceiverAreAnonymous': 'Bool'
        }

    **Those properties list need to be reviewed with the community and the legal team**
    **Along with the privacy policy and ethics agreement of the receivers**

  * **nodeStatisticsDict**, series of arrays containing the node statistics, _need to
    be defined_, and their generation would be controlled by the node administrator.
    Those information goes public.

  * **formFieldsDict**, series of element describing an series of Field using keyword:

        {   'element-name': 'string',
            'element-type': 'Enum',
            'default-value': 'string',
            'required': 'Bool'
        }

  * **moduleDataDict**, is an generic object used to describe flexible object in GLBackend:

        {   'name': '$ID',
            'active': 'Bool',
            'module_type': 'string'
            'module_name': 'string'
            'description': 'string',
            'admin_options': '$formFieldsDict',
            'user_options': '$formFieldsDict',
            'service_message': 'string'
        }

  * **groupDescriptionDict**, is an object used to describe a group of receivers, more than
     one group can exist in the same context (and more context can exist in the same node)
     Another way to see a group is an aggregate view of the TAGS used to describe a receiver.

        {   'group_id' : '$ID',
            'group_name': 'string',
            'description' : '$localizationDict',
            'spoken_language': 'Array, list of spoken languages',
            'group_tags': 'string',
            'receiver_list': 'Array',
            'associated_module': '$moduleDataDict',
            'creation_date': 'Time',
            'update_date': 'Time'
        }

  * /tipStatistics/, composite object containing the stats of a single Tip, concept of
     access and delivery limit need to be supported (or simply unset) inside the
     different modules.

        {   'tip_access_ID': '$ID',
            'tip_title': 'string',
            'last_access': 'Time',
            'last_comment': 'Time',
            'notification_msg': 'string',
            'delivery_msg': 'string',
            'expiration_date': 'Time',
            'pertinence_overall': 'Int',
            'requested_fields': '$formFieldsDict',
            'context_name': 'string',
            'group': '$groupDescriptionDict'
        }

    notification_msg and delivery_msg is the implementation of the old concept
    expressed with:

        'access_limit': 'Int', 'delivery_limit': 'Int',
        'access_performed': 'Int', 'delivery_used': 'Int',

    those elements, in spite of being core feature of the Tip, would be overried
    by specific notification and delivery modules, therefore, also their
    message likely need to be moven in a flexible approach.

    expiration date instead is a core feature system dependent. would be
    postponed, the data can be replicated, but this concept would remain.

  * /tipIndexDict/, this is a block of informations for the receiver, and descrive Tip lists

        {   'tip_access_ID': '$ID',
            'tip_title': 'string',
            'context_ID': '$ID',
            'group_ID': '$ID',
            'notification_adopted': 'string',
            'notification_msg': 'string',
            'delivery_adopted': 'string',
            'delivery_msg': 'string',
            'expiration_date': 'Time',
            'creation_date': 'Time',
            'update_date': 'Time'
        }

  * /contextDescriptionDict/, this series of field contain the description of a
    context. Which data is expected by the whistleblower and which group are
    configured for receive the data. If some module are enabled here and
    policy, description, public information about a context.

        {   'context_id': '$ID'
            'name': '$localizationDict',
            'groups': [ $groupDescriptionDict, {} ],
            'fields': '$formFieldsDict',
            'description': 'string',
            'style': 'string',
            'creation_date': 'Time',
            'update_date': 'Time'
        }

# Details: Requests and Answers

### Addictional resources:

Object specification [[GLBackend/docs/Obj-spec-latest.png]]
Issue tracking [[https://github.com/globaleaks/GLBackend/issues/3]]

### GLBackend REST specification

# example of resources format

`/EXAMPLE/of/RESOURCES/`

    short description of the resource

    :GET
        * Request:
        * Response:

        all the elements not explicited in a resource, has to be intended
        with this behaviour:

        * Response:
          Status Code: 501 (Not implemented)

    :POST
        * Request:
        * Response:
        * Error handling and error codes

    :DELETE
    :PUT
        PUT and DELETE has been implemented in some operations, and
        use a POST (with create or delete boolean parameter) as fallback.


# Resources

P1 `/node/`

Returns information on the GlobaLeaks node. This includes submission paramters and how information should be presented by the client side application.

Follow the resource describing Node (uniq instance, opened to all)

    :GET
        Returns a json object containing all the information of the node.
        * Response:
            Status Code: 200 (OK)
            {
              'name': 'string',
              'statistics': '$nodeStatisticsDict',
              'node_properties': '$nodePropertiesDict',
              'contexts': [ '$contextDescriptionDict', { }, ],
              'description': '$localizationDict',
              'public_site': 'string',
              'hidden_service': 'string',
              'url_schema': 'string'
             }

P2 `/submission`

    :GET
        This creates an empty submission and returns the ID
        to be used when referencing it as a whistleblower.
        ID is a random 64bit integer
        * Response:
          {
              'submission_id': '$ID',
              'creation_time': 'Time'
          }
          Status code: 201 (Created)

        * Error handling:
        If configuration REQUIRE anonymous upload, and the WB is not anonymous
          Status Code: 415 (Unsupported Media Type)
          { 'error_code': 'Int', 'error_message': 'Anonymity required to perform a submission' }

**common behaviour in /submission/<submission_$ID>**

Error handling

    If submission_$ID is invalid
        Status Code: 204 (No Content)
        { 'error_code': 'Int', 'error_message': 'submission ID is invalid' }

P3 `/submission/<submission_$ID>/status`

This interface represent the state of the submission. Will show the
current uploaded data, choosen group, and file uploaded.

permit to update fields content and group selection.

    :GET
        Returns the currently submitted fields, selected group, and uploaded files.
        * Response:
          {
            'fields': '$formFieldsDict',
            'group_matrix': [ '$ID', '$ID' ],
            'uploaded_file': [ '$fileDict', {} ]
            'creation_time': 'Time'
          }

          Would be accepted 'fields' with missing 'Required' fields,
          because the last check is performed in "finalize" interface below.

    :POST
        * Request:
          {
            'fields': '$formFieldsDict',
            'group_matrix': [ '$ID', '$ID' ]
          }

        * Response:
          Status Code: 202 (accepted)

        * Error handling:
          As per "common behaviour in /submission/<submission_$ID/*"
          If group ID is invalid:
            { 'error_code': 'Int', 'error_message': 'group selected ID is invalid' }

P4 `/submission/<submission_$ID>/finalize`

    :POST
        checks if all the 'Required' fields are present, then
        completes the submission in progress and returns a receipt.
        The WB may propose a receipt (because is a personal secret
        like a password, afterall)

        * Request (optional, see "Rensponse Variant" below):
          {
            'proposed-receipt': 'string'
          }

        * Response (HTTP code 200):
          If the receipt is acceptable with the node requisite (minimum length
          respected, lowecase/uppercase, and other detail that need to be setup
          during the context configuration), i saved as authenticative secret for
          the WB Tip, is echoed back to the client Status Code: 201 (Created)

          Status Code: 200 (OK)
          { 'receipt': 'string (with receipt EQUAL to proposed-receipt)' }

        * Response (HTTP code 201):
          If the receipt do not fit node prerequisite, or is missing,
          the submission is finalized, and the server create a receipt.
          The client print back the receipt to the WB.

          Status Code: 201 (Created)
          { 'receipt': 'string' }

        Both response finalize the submission and the only difference is in the HTTP
        return code. This has been discussed (or would be discussed)
        [issue #19, Receipt, proposal of expansion](https://github.com/globaleaks/GLBackend/issues/19)

        * Error handling:
          As per "common behaviour in /submission/<submission_$ID/*"

          If the field check fail
          Status Code: 406 (Not Acceptable)
          { 'error_code': 'Int', 'error_message': 'fields requirement not respected' }

P5 `/submission/<submission_$ID>files`,

    XXX

    This interface supports resume.
    This interface expose the JQuery FileUploader and the REST/protocol
    implemented on it.
    FileUploader has a dedicated REST interface to handle start|stop|delete.
    Need to be studied in a separate way.

    The uploaded files are shown in /status/ with the appropriate
    '$fileDict' description structure.

**At the moment is under research:**
https://docs.google.com/a/apps.globaleaks.org/document/d/17GXsnczhI8LgTNj438oWPRbsoz_Hs3TTSnK7NzY86S4/edit?pli=1

    XXX


T1 `/tip/<uniq_Tip_$ID>` (shared between Receiver and WhistleBlower)

    :GET
        Permit either to WB authorized by Receipt, or to Receivers.
        Both actors have a single, authorized and univoke "t_id".

        Returns the content of the submission with the specified ID.
        Inside of the request headers, if supported, the password for accessing
        the tip can be passed. This returns a session cookie that is then
        used for all future requests to be authenticated.

        * Response:
          Status Code: 200 (OK)
          {
            'fields': '$formFieldsDict',
            'comments': [ { 'author_name': 'string',
                            'date': 'Time',
                            'comment': 'string' },
                          { }
                        ],

            'delivery_method': 'string',
            'delivery_data': 'string',
            'notification_method': 'string',
            'notification_data': 'string',

            'folders': [ { 'id': 'Int' ,
                           'data': 'Time',
                           'description': 'string',
                           'delivery_way' : 'string' },
                         { }
                       ],
            'statistics': '$tipStatistics',
          }

        * Error handling:
          If Tip $ID invalid
          Status Code: 204 (No Content)
          { 'error_code': 'Int', 'error_message': 'requested Tip ID is expired or invalid' }

    :POST
        Used to delete a Tip. Two different kind of removal can exists actually,
        the "personal-delete" remove the Tip of the receiver (or of the whistleblower,
        and "submission-delete" remote all the Tip relative to a specific submission.
        (remove options are present if the users has sufficient priviledges, depends
        on the configuration settings)

        * Request:
        {
            'personal-delete': 'Bool',
            'submission-delete': 'Bool'
        }

        * Response:
          If the user has right permissions:
          the requested content is deleted and:
          Status Code: 200 (OK)

          If the user has not permission:
          Status Code: 204 (No Content)
          { 'error_code': 'Int', 'error_message': 'Operation forbidden' }


T2 `/tip/<uniq_Tip_$ID>/comment` (shared between Receiver and WhistleBlowe)

    Permit either to WB authorized by Receipt, or to Receivers.
    adds a new comment to the submission.

    :POST
        * Request:
            {
                'comment': 'string'
            }

        * Response:
          Status Code: 200 (OK)

        * Error Response, happen when comment are disable:
          Status Code: 204 (No Content)
          { 'error_code': 'Int', 'error_message': 'Operation forbidden' }

        * Error handling
          as per `GET /tip/<uniq_Tip_$ID>/`


T3 `/tip/<uniq_Tip_$ID>/files` (WhistleBlower only)

    perform update operations. If a Material Set has been started, the file is appended
    in the same pack. A Material Set is closed when the `finalize` is called.

    This interface is implemented using (jQueryFileUploader) in the same way of P7

    :GET
        return the unfinalized elements accumulated by the whistleblower. The unfinalized
        material are promoted as 'Set' if the WB do not finalize them before a configurable
        timeout.

        * Request: /
        * Response:
        every object is repeated for every "NOT YET finalized Material Set":
        {
          'finalized-material-date': 'Time',
          'description': 'string',
          'uploaded': [ $fileDict, {} ],
        }

     :POST

        This interface need to be reviewed when jQuery FileUploader,
        and expose the same interface of file

       * Error handling:
         As per jQueryFileUploader
         and as per `/tip/<uniq:_Tip_$ID>/`


T4 `/tip/<uniq_Tip_$ID>/finalize` (WhistleBlowing)

    Used to add description in the Material set not yet completed (optional)
    Used to complete the files upload, completing the Material Set.

    :POST
        * Request:
        { 'description': 'string' }

        Field description is optional

        * Response:
            if files are available to be finalized:
            Status Code: 202 (Accepted)

        * Error handling as per `/tip/<uniq_Tip_$ID>/`


T5 `/tip/<uniq_Tip_$ID>/download` (Receiver - **Delivery module dependent**)

    This REST interface would be likely present, and in future would be moved
    in a separate documentation of optional REST interfaces. Is implemented by
    the module 'delivery_local' (default module for delivery), has the property
    to permit a limited amount of download, an then invalidate itself.

    Used to download the material from the
    submission. Can only be requested if the user is a Receiver and the
    relative download count is < max_downloads.

    :GET
        * Request:
             { 'folder_ID': '$ID' }

        * Response:
             Status Code: 200 (OK)


T6 `/tip/<uniq_Tip_$ID>/pertinence` (Receiver only)

    Optional (shall not be supported by configuration settings)
    express a vote on pertinence of a certain submission.
    This can only be done by a receiver that has not yet voted.

    :POST
        * Request:
          { 'pertinence-vote': 'Bool' }

        * Response:
          Status Code: 202 (Accepted)
        _ Error handling as per `/tip/<string t_id>/`


# Receiver API

R1 `/receiver/<uniq_Tip_$ID>/overview`

This interface expose all the receiver related info, require one valid Tip authentication.
This interface returns all the options available for the receiver (notification and delivery)
and contain the require field (empty or compiled)

depends from the node administator choose and delivery/notification extension, the capability
to be configured by the user.

(tmp note: overview is the replacement of the previous release "Bouquet")
note, this access model imply that a receiver can configured their preferences only having a
Tip opened for him. This default behaviour would be overrided by modules.

    :GET
       * Response:
         Stauts Code: 200 (OK)
         {
             'tips': [ '$tipIndexDict', { } ]
             'notification-method': [ '$moduleDataDict', { } ],
             'delivery-method': [ '$moduleDataDict', { }  ],
             'receiver-properties': '$receiverDescriptionDict'
         }

    :(GET and POST)
        * Error code:
        _ If t_id is invalid
          Status Code: 204 (No Content)
          { 'error_code': 'Int', 'error_message': 'requested Tip ID is expired or invalid' }

R2 `/receiver/<string t_id>/<string module_type>`

Every module need a way to specify a personal interface where receive preferences, this would be
used in Notification and Delivery modules.

    The REST concept is the CURD used in A2,A3,A4

    <module_type> assume, for R2, only two kind of types:
    'notification'
    'delivery'

    :GET
        * Response:
          Status Code: 200 (OK)
          {
              'modules': [ '$moduleDataDict', {} ]
          }

    :POST
        * Request:
          {
              'create': 'Bool',
              'delete': 'Bool',
              'module': '$moduleDataDict'
          }

    :PUT
        * Request:
          {
              'module': '$moduleDataDict'
          }

    :DELETE
        * Request:
          {
              'module': '$moduleDataDict'
          }

# Admin API

**common behaviour in Admin resorces**

    The following API has a shared element: they have a GET, that return
    the list of the resource data, and a POST, that await for a single
    instance of a data, and two optional boolean 'create' and 'delete'.
    Every instance of data has an $ID inside, the identify in an unique
    way the object.

    :POST
      * Request
      {
          'create': 'Bool',
          'delete': 'Bool',
          'example': '$SpecificObject'
      }

      * Response

    if 'create' is True,
        SpecificObjet['id'] is ignored, SpecificObject is copied and a new resource created.
        return as GET

    if 'delete' is True
        if SpecificObject['id'] exists
            the context is deleted
            return as GET
        else
            Error Code 400 (Bad Request)
            { 'error_code': 'Int', 'error_message' : 'Invalid $ID in request' }

    if SpecifiedObject['id'] exists
        if 'create' AND 'delete' are False
            the context is updated
            return as GET
        else
            Error Code 400 (Bad Request)
            { 'error_code': 'Int', 'error_message' : 'Invalid $ID in request' }


A1 `/admin/node`

    The Get interface is thinked as first blob of data able to present the node,
    therefore not all the information are specific of this resource (like
    contexts description or statististics), but for reduce the amount of request
    performed by the client, has been collapsed into.

    :GET
        Returns a json object containing all the information of the node.
        * Response:
            Status Code: 200 (OK)
            {
              'name': 'string',
              'statistics': '$nodeStatisticsDict',
              'private_stats': { },
              'node_properties': '$nodePropertiesDict',
              'contexts': [ '$contextDescriptionDict', { }, ],
              'description': '$localizationDict',
              'public_site': 'string',
              'hidden_service': 'string',
              'url_schema': 'string'
             }

        'private_stats' need do be defined, along with $nodeStatisticsDict.

    :POST
        Changes the node public node configuration settings
        * Request:
            {
              'name': 'string',
              'node_properties': '$nodePropertiesDict',
              'description': '$localizationDict',
              'public_site': 'string',
              'hidden_service': 'string',
              'url_schema': 'string'

              'enable_stats': [ ],
              'do_leakdirectory_update': 'Bool',
              'new_admin_password': 'string',

             }

        'enable_stats' need to be defined along with $nodeStatisticsDict.

    This interface does not return an error, except as wrong authentication,
    need to be readed: http://twistedmatrix.com/documents/10.1.0/web/howto/web-in-60/http-auth.html


A2 `/admin/contexts/`

    List, create, delete and update all the contexts in the Node.

    :GET
        Returns a json object containing all the contexts information.
        * Response:
          Status Code: 200 (OK)
        {
          'contexts': [ '$contextDescriptionDict', { } ]
        }

    :POST
        * Request:
          Implements the fallback if PUT and DELETE method do not work
        {
          'create': 'Bool',
          'delete': 'Bool',
          'context': '$contexDescriptionDict',
        }

    :DELETE
        Remove an existing context, same effect of POST with delete = True
        {
          'context': '$contexDescriptionDict'
        }

    :PUT
        Create a new context, same effect of POST with create = True
        {
          'context': '$contexDescriptionDict'
        }

        * Response:
          As per **common behaviour in Admin resorces**

A3 `/admin/group/<context_$ID>/`

    Retrive, create, update or delete the target group
    (the context_$ID or name are supposed previously obtained by `/admin/contexts/`
    or `/admin/node/`, having every context one or more group, you can access all of
    them from this interface)

    :GET
       Returns a json object listing the available group and the available modules
       * Response:
            {
                'groups': '$groupDescriptionDict',
                'modules_available': [ '$moduleDataDict', { } ]
            }

        receiver_module need to be specified always, does not exist a group
        without a module that define how the receiver list has been retrivered.
        confiuration_type is a string depending from the configured module used to
        retrive receivers list in the group.

    :POST
        Implement the fallback in PUT|DELETE method
       * Request:
            {
                'group': '$groupDescriptionDict',
                'create': 'Bool',
                'delete': 'Bool',
            }

    :PUT
        * Request:
          Create a new group, same effect of POST with create = True
            {
                'group': '$groupDescriptionDict'
            }
    :DELETE
        * Request:
          Delete the selected group, same effect of POST with delete = True
            {
                'group': '$groupDescriptionDict'
            }

         If group_id is missing, is created a new one
         If group_id is present, are updated the current data

       * Response:
          As per **common behaviour in Admin resorces**


A4 `/admin/receiver/<group_$ID>/`

    All the operations, in case of wrong group_$ID, return:
        Error Code 400 (Bad Request)
        { 'error_code': 'Int', 'error_message': Invalid group ID' }

    :GET
        Returns a json object containing all the receivers information,
        coherently to the module requested.

        * Response:
          Status Code 200 (OK)
            {
               'receivers' : [ '$receiverDescriptionDict', { } ]
            }

          In this case, the remote ticketing system module, has not a single receiver
          confiugured.
          This module is configured to describe a specific group, and when the users
          of this group need to be contacted, the module relay. the properties are
          UnSet because not used (the submission is dispatch in a remote system).

    :POST
        * Request:
          update or create a new receiver (if permitted) in the associated module,
          works as fallback if PUT or DELETE method are not usable.
            {
              'delete': 'Bool',
              'create: 'Bool',
              'receiver': '$receiverDescriptionDict'
            }

    :DELETE
        delete an available receiver, in the selected module/group,
        same effect of POST with delete = True
        * Request:
            {
              'receiver': '$receiverDescriptionDict'
            }

    :PUT
        create a new receiver (if available), in the selected module/group
        same effect of POST with create = True
        * Request
            {
              'receiver': '$receiverDescriptionDict'
            }

       * Response:
          As per **common behaviour in Admin resorces**

          If something goes wrong due to the interal checks of the module:
            Error Code 501 (Not Implemented)
            { 'error_code': 'Int', 'error_message' : 'module error details' }


A5 `/admin/modules/<string module_type>/`

These interface permit to list, configure, enable and disasble all the
available modules.
The modules are flexible implementation extending a specific part of GLBackend,
The modules would be part of a restricted group of elements:

    TODO PUT HERE THE LIST OF EXTENDABLE ABSTRACT CLASS
    BECAUSE THEY ARE ALSO THE "TYPES" WHERE A MODULE NEED TO FIT INTO

    and all of those keyword need to be requested in the REST interface,
    actually are:

    "notification"
    "delivery"
    "inputfilter"
    "tip"
    "receiver"
    "filestorage"
    "databasestorage"

    :GET
        * Response:
        {
          'modules_available': [ '$moduleDataDict', { } ]
          'context_applied': {
                      'module_$ID': [ 'context_$ID', 'context_$ID' ],
                      { } }
        }

    :POST
        * Request:
        {
          'status': 'Bool',
          'targetContext': [ 'context_$ID', 'context_$ID' ],
          'module_settings': '$moduleDataDict'
        }

        * Response:

          'status' if is True mean that the module would be activated,
          else, is False, mean that the module would be deactivated.
          The previous status of the module is not checked, but during
          the activation some module dependend check may fail, in those
          cases:

            Error Code 501 (Not Implemented)
              { 'error_code': 'Int', 'error_message' : 'module error details' }

          Otherwise, if request is accepted:
            Status Code 200 (OK)
