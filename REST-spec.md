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
Id is a random 64bit integer (POST only)

P3 `/submission/<submission_id>`

Returns the currently submitted fields and material filenames and size, this is the only interface giving back the complete submission status (GET only)

P4 `/submission/<submission_id>/submit_fields`

does the submission of the fields that are supported by the node in question and update the selected submission_id (POST only)

P5 `/submission/<submission_id>/submit_group`

Optional Interface (may not be provided by Node Options) select the groups into the list of recipients for the selected submission. 
Group are addressed by their Id (POST only) 

P6 `/submission/<submission_id>/finalize`

Completes the submission in progress, **give to the server the receipt secret** and confirm the receipt (or answer with a part of them). settings dependent.  (POST only)

P7 `/submission/<submission_id>/upload_file`

upload a file to the selected submission_id (REST depends from JQueryFileUpload integration)

### API shared between WhistleBlowers and Receiver (require auth)

T1 `/tip/<string auth t_id>`

Returns the content of the submission with the specified Id.
Inside of the request headers, if supported, the password for accessing the tip can be passed. 
This returns a session token that is then used for all future requests to be authenticated. 
Supports GET (all status data), POST (comment and pertinence)

T2 `/tip/<uniq_Tip_$ID>/add_comment`

Both WB and Receiver can write a comment in a Tip (POST only)

### Tip subsection API (WhistleBlower only)

T3 `/tip/<uniq_Tip_$ID>/update_file`

Add a new folder files in the associated submission, (update the Tip for all the
receiver, in regards of the modules supports)
The material is published when 'finalized'.
(GET, POST)

T4 `/tip/<string t_id>/finalize_update`

Used to add a description in the uploaded files. 
This action make the new uploaded data available for download. 
If this action is missed, the material can be published after a timeout expiring 
at midnight (MAY BE REVIEWED) (POST only)

### Tip subsection (API Receivers only)

T5 `/tip/<string t_id>/download_material`

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

Having the group_$ID


A5 `/admin/modules/<string module_type>/`

as defined in [issue #15](https://github.com/globaleaks/GLBackend/issues/15), there
are various flexible section of GLBackend configurable and choosable by the 
administrator. Here would be listed, selected and configured. Every module
is a python file present in the running code, update the modules list would require
a remote access.

# Synthesis 

`/node/`

`/submission`
`/submission/<submission_$ID>/status`
`/submission/<submission_$ID>/upload_file`
`/submission/<submission_$ID>/finalize`

`/receiver/<string t_id>/overview`
`/receiver/<string t_id>/<string module_name>`

`/admin/contexts/`
`/admin/group/<context_$ID>/`
`/admin/receivers/<group_$ID>/`
`/admin/modules/<string module_type>/`
`/admin/node/`

_Note: all the Tip interfaces depends on Tip implementation, the presented interface are the default Tip_

`/tip/<uniq_Tip_$ID>`
`/tip/<uniq_Tip_$ID>/add_comment`
`/tip/<uniq_Tip_$ID>/update_file`
`/tip/<uniq_Tip_$ID>/finalize_update`
`/tip/<uniq_Tip_$ID>/pertinence`
`/tip/<uniq_Tip_$ID>/download_material`

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
    'String'
    'Bool', True|False

    { 'key' : 'value' }, a tuple
    [ 'elem1', 'elem2', 'elem3' ] an array of elements

Exists also some complex datatype, they are written in this document with the "$" in front
of the datatype-name, the list and the detailed meaning would be found in:
[issue #14](https://github.com/globaleaks/GLBackend/issues/14), this is the reference.

  * **ID**: Identified, is an unique value amount the same kind of data, and would be
    and integer or a string user choosen. The property of the Id is to be unique.

  * **File**: file descriptor element, every file (uploaded or available in download) is 
    represented with this dict:

        {   'filename': <String>, 
            'comment': <String>, 
            'size': 'Int', 
            'content-type': 'String',
            'date': 'Time',
            'CleanedMetaData': 'enum' 
        }

  * **LocalDict**: the Local Dict is an object used to store localized texts, in example:

        {   'IT' : 'Io mi chiamo Mario.',
            'EN' : 'Is a me, Mario!!1!',
            'FR' : "je m'appelle Marìò, pppffff"
        }

  * **ReceiverDesc**, series of tuple with boolean values, expressing the permissions given 
    to a receiver, and series of descriptive data for the single receiver.

    **Those properties list need to be reviewed with the community and the legal team**

        {   'ReceiverID': '$ID',
            'CanDeleteSubmission': 'Bool',
            'CanPostponeExpiration': 'Bool',
            'CanConfigureNotification': 'Bool',
            'CanConfigureDelivery': 'Bool',
            'receiver_name': 'String',
            'receiver_description': 'String',
            'receiver_tags': 'String',
            'contact_data': 'String',
            'creation_date': 'Time',
            'update_date': 'Time'
            'module_id': $ID,
            'module_dependent_data': '$FormFields',
            'module_dependent_stats': 'Array'
        }

    This element may contain sensitive data: is exposed only in administrative interfaces
    and personal management interface (/receivers/...)


  * **NodeProperties**, series of tuple with boolean value, expressing the property
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

  * **NodeStats**, series of arrays containing the node statistics, _need to
    be defined_, and their generation would be controlled by the node administrator.
    Those information goes public.

  * **FormFields**, series of element describing an series of Field using keyword:

        {   'element-name': 'String', 
            'element-type': 'Enum', 
            'default-value': 'String',
            'required': 'Bool' 
        }

  * **ModuleDataStruct**, is an generic object used to describe flexible object in GLBackend:

        {   'name': '$ID', 
            'active': 'Bool', 
            'module_type': 'String'
            'module_name': 'String'
            'description': 'String',
            'admin_options': '$FormFields',
            'user_options': '$FormFields',
            'service-message': 'String'
        }

  * **GroupDescription**, is an object used to describe a group of receivers, more than
     one group can exist in the same context (and more context can exist in the same node)
     Another way to see a group is an aggregate view of the TAGS used to describe a receiver.

        {   'group_id' : '$ID',
            'group_name': 'String',
            'description' : 'LocaLDict',
            'spoken_language': 'Array, list of spoken languages',
            'group_tags': 'String',
            'receiver_list': 'Array',
            'group_id': 'String',
            'associated_module': '$ModuleDataStruct',
            'creation_date': 'Time',
            'update_date': 'Time'
        }

  * /TipStats/, composite object containing the stats of a single Tip, concept of 
     access and delivery limit need to be supported (or simply unset) inside the
     different modules.

        {   'tip_access_ID': '$ID',
            'tip_title': 'String',
            'last_access': 'Time',
            'last_comment': 'Time',
            'notification_msg': 'String',
            'delivery_msg': 'String',
            'expiration_date': 'Time',
            'pertinence_overall': 'Int',
            'requested_fields': '$FormFields',
            'context_name': 'String',
            'group': '$GroupDescription'
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

  * /TipIndex/, this is a block of informations for the receiver, and descrive Tip lists

        {   'tip_access_ID': '$ID', 
            'tip_title': 'String',
            'context_ID': '$ID',
            'group_ID': '$ID',
            'notification_adopted': 'String',
            'notification_msg': 'String',
            'delivery_adopted': 'String',
            'delivery_msg': 'String',
            'expiration_date': 'Time',
            'creation_date': 'Time',
            'update_date': 'Time'
        }

  * /ContexDescription/, this series of field contain the description of a
    context. Which data is expected by the whistleblower and which group are
    configured for receive the data. If some module are enabled here and 
    policy, description, public information about a context.

        {   'context_id': '$ID'
            'name': 'LocaLDict',
            'groups': [ $GroupDescription, {} ],
            'fields': '$FormFields',
            'description': 'String',
            'style': 'String',
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
        no PUT, DELETE and other methods beside GET and POST has been 
        implemented in his REST. This choose is an adaptation to
        some proxy limits.


# Resources

`/node/`

Returns information on the GlobaLeaks node. This includes submission paramters and how information should be presented by the client side application.

Follow the resource describing Node (uniq instance, opened to all)

    :GET
        Returns a json object containing all the information of the node.
        * Response:
            Status Code: 200 (OK)
            {
              'name': 'String',
              'statistics': '$NodeStats',
              'node_properties': '$NodeProperties',
              'contexts': [ '$ContextDescription', { }, ],
              'description': '$LocalDict',
              'public_site': 'String',
              'hidden_service': 'String',
              'url_schema': 'string'
             }

`/submission`

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

`/submission/<submission_$ID>/status`

This interface represent the state of the submission. Will show the
current uploaded data, choosen group, and file uploaded.

permit to update fields content and group selection.

    :GET
        Returns the currently submitted fields, selected group, and uploaded files.
        * Response:
          { 
            'fields': '$FormField',
            'group_matrix': [ '$ID', '$ID' ],
            'uploaded_file': [ '$File', {} ]
            'creation_time': 'Time'
          }

          Would be accepted 'fields' with missing 'Required' fields,
          because the last check is performed in "finalize" interface below.

    :POST
        * Request:
          { 
            'fields': '$FormField',
            'group_matrix': [ '$ID', '$ID' ]
          }

        * Response:
          Status Code: 202 (accepted)

        * Error handling:
          As per "common behaviour in /submission/<submission_$ID/*"
          If group ID is invalid:
            { 'error_code': 'Int', 'error_message': 'group selected ID is invalid' }


`/submission/<submission_$ID>/finalize`, 

    :POST
        checks if all the 'Required' fields are present, then 
        completes the submission in progress and returns a receipt.
        The WB may propose a receipt (because is a personal secret 
        like a password, afterall)

        * Request (optional, see "Rensponse Variant" below):
          { 
            'proposed-receipt': 'String'
          }

        * Response (HTTP code 200):
          If the receipt is acceptable with the node requisite (minimum length
          respected, lowecase/uppercase, and other detail that need to be setup
          during the context configuration), rs saved as authenticative secret for 
          the WB Tip, is echoed back to the client Status Code: 201 (Created)

          Status Code: 200 (OK)
          { 'receipt': 'String' }

        * Variant Response (HTTP code 201):
          If the receipt do not fit node prerequisite, or is expected but not provide
          the submission is finalized, and the server create a receipt. 
          The client print back to the WB, who record that 

          Status Code: 201 (Created)
          { 'receipt': 'String' }


        * Error handling:
          As per "common behaviour in /submission/<submission_$ID/*"

          If the field check fail
          Status Code: 406 (Not Acceptable)
          { 'error_code': 'Int', 'error_message': 'fields requirement not respected' }


`/submission/<submission_$ID>/upload_file`, 

    XXX

    This interface supports resume. 
    This interface expose the JQuery FileUploader and the REST/protocol
    implemented on it.
    FileUploader has a dedicated REST interface to handle start|stop|delete.
    Need to be studied in a separate way.

    The uploaded files are shown in /status/ with the appropriate
    '$File' description structure.

    XXX


`/tip/<uniq_Tip_$ID>` (shared between Receiver and WhistleBlower)

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
            'fields': '$FormFields',
            'comments': [ { 'author_name': 'String',
                            'date': 'Time',
                            'comment': 'String' },
                          { }
                        ],

            'delivery_method': 'String',
            'delivery_data': 'String',
            'notification_method': 'String',
            'notification_data': 'String',

            'folders': [ { 'id': 'Int' ,
                           'data': 'Time',
                           'description': 'String',
                           'delivery_way' : 'String' },
                         { }
                       ],
            'statistics': '$TipStats',
          }

        * Error handling:
          If Tip $ID invalid
          Status Code: 204 (No Content)
          { 'error_code': 'Int', 'error_message': 'requested Tip ID is expired or invalid' }

    :POST
        Used to delete a submission if the users has sufficient priviledges.
        Administrative settings can configure if all or some, receivers or
        WB, can delete the submission. (by default they cannot).

        * Request:
        {
            'delete': 'Bool'
        }

        * Response:
          If the user has right permissions:
          Status Code: 200 (OK)

          If the user has not permission:
          Status Code: 204 (No Content)


`/tip/<uniq_Tip_$ID>/add_comment` (shared between Receiver and WhistleBlowe)

    Permit either to WB authorized by Receipt, or to Receivers.
    adds a new comment to the submission.

    :POST
        * Request:
            {
                'comment': 'String' 
            }

        * Response:
          Status Code: 200 (OK)
        * Error handling 
          as per `GET /tip/<uniq_Tip_$ID>/`


`/tip/<uniq_Tip_$ID>/update_file` (WhistleBlower only)

    perform update operations. If a Material Set has been started, the file is appended
    in the same pack. A Material Set is closed when the `finalize_update` is called.

    :GET
        return the unfinalized elements accumulated by the whistleblower. The unfinalized
        material are promoted as 'Set' if the WB do not finalize them before a configurable
        timeout.

        * Request: /
        * Response:
        every object is repeated for every "NOT YET finalized Material Set":
        { 
          'finalized-material-date': 'Time',
          'description': 'String',
          'uploaded': [ $File, {} ],
        }

     :POST

        This interface need to be reviewed when jQuery FileUploader,
        and expose the same interface of upload_file

       * Error handling:
         As per jQueryFileUploader
         and as per `/tip/<uniq:_Tip_$ID>/`


`/tip/<uniq_Tip_$ID>/finalize_update` (WhistleBlowing)

    Used to add description in the Material set not yet completed (optional)
    Used to complete the files upload, completing the Material Set.

    :POST
        * Request:
        { 'description': 'String' }

        Field description is optional

        * Response:
            if files are available to be finalized:
            Status Code: 202 (Accepted)

        * Error handling as per `/tip/<uniq_Tip_$ID>/`


`/tip/<uniq_Tip_$ID>/download_material` (Receiver - **Delivery module dependent**)

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


`/tip/<uniq_Tip_$ID>/pertinence` (Receiver only)

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

`/receiver/<uniq_Tip_$ID>/overview`

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
             'Tips': [ '$TipIndex', { } ]
             'notification-method': [ '$ModuleDataStruct', { } ],
             'delivery-method': [ '$ModuleDataStruct', { }  ],
             'receiver-properties': '$ReceiverDesc'
         }

    :(GET and POST)
        * Error code:
        _ If t_id is invalid
          Status Code: 204 (No Content)
          { 'error_code': 'Int', 'error_message': 'requested Tip ID is expired or invalid' }

`/receiver/<string t_id>/<string module_name>`

Every module need a way to specify a personal interface where receive preferences, this would be
used in Notification and Delivery modules.

    :GET 
        * Response:
          Status Code: 200 (OK)
          {
              'module_description': '$LocalDict'
              'pref': '$ModuleDataStruct'
          }

    :POST
          {
              'pref': '$ModuleDataStruct'
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


`/admin/contexts/`

    List, create, delete and update all the contexts in the Node.

    :GET
        Returns a json object containing all the contexts information.
        * Response:
          Status Code: 200 (OK)
        {
          'contexts': [ '$ContextDescription', { } ]
        }

    :POST
        * Request:
          Status Code: 200 (OK)
        { 
          'create': 'Bool',
          'delete': 'Bool',
          'context': '$ContexDescription',
        }

        * Response:
          As per **common behaviour in Admin resorces**

`/admin/group/<context_$ID>/`

    Retrive, create, update or delete the target group 
    (the context_$ID or name are supposed previously obtained by `/admin/contexts/` 
    or `/admin/node/`, having every context one or more group, you can access all of
    them from this interface)

    :GET
       Returns a json object listing the available group and the available modules 
       * Response:
            {
                'groups': '$GroupDescription',
                'modules_available': [ '$ModuleDataStruct', { } ]
            }

        receiver_module need to be specified always, does not exist a group
        without a module that define how the receiver list has been retrivered.
        confiuration_type is a string depending from the configured module used to 
        retrive receivers list in the group.

    :POST
       * Request:
            {
                'group': '$GroupDescription',
                'create': 'Bool',
                'delete': 'Bool',
            }

         If group_id is missing, is created a new one 
         If group_id is present, are updated the current data

       * Response:
          As per **common behaviour in Admin resorces**


`/admin/receiver/<group_$ID>/`

    All the operations, in case of wrong group_$ID, return:
        Error Code 400 (Bad Request)
        { 'error_code': 'Int', 'error_message': Invalid group ID' }
 
    :GET
        Returns a json object containing all the receivers information,
        coherently to the module requested.

        * Response:
          Status Code 200 (OK)
            {
               'receivers' : [ '$ReceiverDesc', { } ]
            }

          In this case, the remote ticketing system module, has not a single receiver 
          confiugured.
          This module is configured to describe a specific group, and when the users 
          of this group need to be contacted, the module relay. the properties are 
          UnSet because not used (the submission is dispatch in a remote system).

    :POST
        * Request:
          update or create a new receiver (if permitted) in the associated module
            {
              'delete': 'Bool',
              'create: 'Bool',
              'receiver': '$ReceiverDesc'
            }

       * Response:
          As per **common behaviour in Admin resorces**

          If something goes wrong due to the interal checks of the module:
            Error Code 501 (Not Implemented)
            { 'error_code': 'Int', 'error_message' : 'module error details' }


`/admin/modules/<string module_type>/`

These interface permit to list, configure, enable and disasble all the 
available modules.
The modules are flexible implementation extending a specific part of GLBackend,
The modules would be part of a restricted group of elements:

    TODO METTI QUI LA LISTA DELLE ABSTRACT CLASS

and one of those keyword need to be requested in the REST interface.


    :GET
        * Response:
        {
          'modules_available': [ '$ModuleDataStruct', { } ]
          'context_applied': { 
                      'module_$ID': [ 'context_$ID', 'context_$ID' ], 
                      { } }
        }

    :POST
        * Request:
        {
          'status': 'Bool',
          'targetContext': [ 'context_$ID', 'context_$ID' ],
          'module_settings': '$ModuleDataStruct'
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

`/admin/node`

    :GET
        Returns a json object containing all the information of the node.
        * Response:
            Status Code: 200 (OK)
            {
              'name': 'String',
              'statistics': '$NodeStats',
              'private_stats': { },
              'node_properties': '$NodeProperties',
              'contexts': [ '$ContextDescription', { }, ],
              'description': '$LocalDict',
              'public_site': 'String',
              'hidden_service': 'String',
              'url_schema': 'string'
             }

        'private_stats' need do be defined, along with $NodeStats.

    :POST
        Changes the node public node configuration settings
        * Request:
            {
              'name': 'String',
              'node_properties': '$NodeProperties',
              'description': '$LocalDict',
              'public_site': 'String',
              'hidden_service': 'String',
              'url_schema': 'string'

              'enable_stats': [ ],
              'do_leakdirectory_update': 'Bool',
              'new_admin_password': 'String',

             }

        'enable_stats' need to be defined along with $NodeStats.
