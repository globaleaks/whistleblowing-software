# Summary

This is a breif summary of the REST API specification.

## Public API

### API accessible at all users

`/node/`

Returns information on the GlobaLeaks node. This includes
submission paramters and how information should be presented
by the client side application.

`/submission`

This creates an empty submission and returns the ID
to be used when referencing it as a whistleblower.
ID is a random 64bit integer (POST only)

`/submission/<submission_id>`

Returns the currently submitted fields and material filenames and size, this
is the only interface giving back the complete submission status (GET only)

`/submission/<submission_id>/submit_fields`

does the submission of the fields that are supported by
the node in question and update the selected submission_id (POST only)

`/submission/<submission_id>/add_group`

adds a group to the list of recipients for the selected
submission. group are addressed by their ID (POST only)

`/submission/<submission_id>/finalize`

completes the submission in progress, **give to the server the receipt secret**
and confirm the receipt (or answer with a part of them). settings dependent.
(POST only)

`/submission/<submission_id>/upload_file`

upload a file to the selected submission_id (PUT only)

### API shared between WhistleBlowers and Receiver (require auth)

`/tip/<string auth t_id>`

Returns the content of the submission with the specified ID.
Inside of the request headers, if supported, the password for accessing
the tip can be passed. This returns a session token that is then
used for all future requests to be authenticated. supports
GET (all status data), POST (comment and pertinence), DELETE tip (if 
permitted by configuration)

`/tip/<string t_id>/add_comment`

Both WB and Receiver can write a comment in a Tip (POST only)

### tip subsection API (WhistleBlower only)

`/tip/<string t_id>/update_file`

Update material available for download, a new material has resetted 
counter for download limits. 
The material is published when 'finalized'. (PUT, GET, DELETE)

`/tip/<string t_id>/finalize_update`

Used to add a description in the uploaded files. 
This action make the new uploaded data available for download. 
If this action is missed, the material can be published after a timeout expiring 
at midnight (MAY BE REVIEWED) (POST only)

### tip subsection (API Receivers only)

`/tip/<string t_id>/download_material`

This interface can be disabled by delivery configuration.

used to download the material from the
submission. if a download limit has been configured, can be requested
only if relative download count is < max_downloads (POST only).

Paramters inside the POST specify which Material Set and the requested
mode (compressed, encrypted)

`/tip/<string t_id>/pertinence`

This interface can be disabled by administrative settings.
express a pertinence value (-1 or +1, True/False) (POST only)

## Receiver API

`/receiver/<string t_id>/overview`

Brief summary of all related Tip, and personal settings customizable by
the receiver.

## Admin API

`/admin/receivers/`

Interact with the current receivers list, the GET is supported and 
not intended to be redoundand with GET /node/, because maybe the 
public output shall be different from the admin capability of view (GET, POST)

`/admin/node`

For configuring the *public* details of the node, the private details are
set in the specific resources

`/admin/delivery`
`/admin/notification`

For setting up delivery and notification modules. perform host dependent
configuration.

`/admin/config/storage`

For setting up storage methods.

# Synthesis 

`/node/`

`/submission`
`/submission/<submission_id>`
`/submission/<submission_id>/submit_fields`
`/submission/<submission_id>/add_group`
`/submission/<submission_id>/finalize`
`/submission/<submission_id>/upload_file`

`/tip/<string auth t_id>`
`/tip/<string t_id>/add_comment`
`/tip/<string t_id>/update_file`
`/tip/<string t_id>/finalize_update`
`/tip/<string t_id>/download_material`
`/tip/<string t_id>/pertinence`

`/receiver/<string t_id>/overview`

`/admin/receivers/`
`/admin/node`
`/admin/delivery`
`/admin/notification/`
`/admin/storage/`

# Data Object involved

file descriptor, every completed file upload is always stored and represented with this dict:

    { filename: <string>, comment: <String>, size: <Int, in bytes>, content-type: <string> }

<LocaLDict>, the Local Dict is an object used to store localized texts, in example:

    { 'IT' : 'Sono io, Mario!' },
    { 'EN' : 'Mario am I!' },
    { 'FR' : 'je suis Mario!' }


<RDict>, an object of boolean values, expressing the permissions given to a receiver, 
         They need to be specified separately. Possible permissions can be:
         . can delete a submission (not just a Tip)
         . can postopone expiration date
         . can configure his own notification settings
         . can configure his own delivery settings

<NDict>, an object of booleand values, expressing the properties of the node,
         They need to be specified separately.
         Those properties likey can be communicated to an external directory 
         (LeakDirectory) and express the safety, the features and the reliability
         of a GL node. 
         Possible properties can be:
         . end to end encryption enforced,
         . are receivers part of the admin group ?
         . anonymity enforced ?
         . are the receivers identity published ?

<ModuleDataStruct>, is an object used to describe the current status of a 

    [ 'name': <String>, 
      'active': <Bool>, 
      'options': <Form fields>,
      'service-message': <String>
    ]

<ModuleAdminConfig>, basically has the same field of <ModuleDataStruct>, except:
    . it contains the field that need to be configured once per node, by the admin
      the 'options' fields therefore differ from the 'options' in ModuleDataStruct
    . the active: True|False cause the activation of the module for the receiver

ModuleAdminConfig is used in the REST of /admin/* path, ModuleDataStruct in /receiver/*

# Details: Requests and Answers

### Addictional resources:

Object specification [[GLBackend/docs/Obj-spec-latest.png]]
Issue tracking [[https://github.com/globaleaks/GLBackend/issues/3]]

### GLBackend REST specification

`/node/`

    Returns information on the GlobaLeaks node. This includes
    submission paramters and how information should be presented
    by the client side application.

    Follow the resource describing Node (uniq instance, opened to all)

    :GET
        Returns a json object containing all the information of the node.
        * Response:
            Status Code: 200 (OK)
            {
              'name': <LocaLDict Name of the initiative>,
              'statistics': <Array - To be defined, general statistics>,
              'node-properties': <NDict>,
              'contexts': [
                           {'name': <LocaLDict name of context>,
                            'groups': [
                              { 'id': <Int>, 'description' : '<LocaLDict description>', 
                               'name' : '<LocaLDict title>', lang: '<Array, list of supported lang>' }
                              { 'id': <Int>, 'description' : '<LocaLDict description>', 
                               'name' : '<LocaLDict title>', lang: '<Array, list of supported lang>' } ]
                            'fields': [
                              { 'name' : <LocaLDict field>, type: (txt|int|img), 'Required': <Bool> },
                              { 'name' : <LocalDict field>, type: (txt|int|img), 'Required': <Bool> } ]
                            },
               'description': <LocalDict, descrption headline>,
               'public_site': <string, url>,
               'hidden_service': <string, url.onion>,
             }
        example of a result:
             {
              'name': "blue meth fighting in alberoque",
              'statistics': <string, general statistics>,
              'node-properties': <end2end_encryption: Yes, Anonymous_receiver: Yes>,
              'contexts': [
                            { 'name' : 'Heisenberg sightings',
                              'groups' : [ 
                                    { 'id' : 0, name : 'police', description: 'Our national strength',
                                        lang: 'EN, ES' },
                                    { 'id' : 1, name : 'vigilantes', description: 'Batman progeny',
                                        lang, 'IT, PT, LT, EN, ES' } ],
                              'fields': [ { 'name': 'headline', 'type':'text', 'Required': True },
                                          { 'name': 'photo', 'type':'img', 'Required':False },
                                          { 'name': 'description', 'type': 'txt', 'Required':True }, ]
                            },
                            {'name': 'Crystal Meth report',
                              'groups': [ { 0 : 'police' , 1 : 'journalists', 2 : 'Municipality'} ],
                              'fields': [ { 'name': 'headline', 'type':'text', 'Required': True },
                                          { 'name': 'proof', 'type':'file', 'Required':True },
                                          { 'name': 'description', 'type': 'txt', 'Required':True }, ]
                            }
                          ]
               'description': 'This node aggregate expert of the civil society in fighting the crystal meth, producted by the infamous Heisenberg',
               'public_site': 'http://fightmeth.net',
               'hidden_service': 'vbg7fb8yuvewb9vuww.onion',
              }
    :POST
        None
        * Reponse:
          Status Code: 501 (Not implemented)

    :DELETE
        None
        * Reponse:
          Status Code: 501 (Not implemented)

    :PUT
        None
        * Reponse:
          Status Code: 501 (Not implemented)


`/submission`

    :GET
        None
        * Response:
          Status Code: 501 (Not implemented)

    :POST
        This creates an empty submission and returns the ID
        to be used when referencing it as a whistleblower.
        ID is a random 64bit integer
        * Response:
          { 'submission_id': ID }
          Status code: 201 (Created)

        _ If configuration REQUIRE anonymous upload, and the WB is not anonymous
          Status Code: 415 (Unsupported Media Type)
          { error-code: <Int>, error-details: 'Anonymity required to perform a submission' }


`/submission/<submission_id>`

    :GET
        Returns the currently:
            submitted fields 
            material filenames and size,
            group selection status

        This is the only interfaces which return the entire status of the submission.
        the time is not yet finalized, therefore is saved the time of the first upload

        * Response:

          [ 'material-date': <DATE, 32bit time value>,
           { filename: <string>, comment: <String>, size: <Int, in bytes>, content-type: <string> }
           { filename: <string>, comment: <String>, size: <Int, in bytes>, content-type: <string> }
          ], [
           { group-one: True, group-two: False, group-three: True } 
          ], [
           {'field_name1': <content>},
           {'field_name2': <content>}
          ]
          Status Code: 200

        _ If submission_id is invalid
          Status Code: 204 (No Content)
          { error-code: <Int>, error-message: 'submission ID is invalid' }


`/submission/<submission_id>/submit_fields`

    :POST
        `/submit_fields`, does the submission of the fields that are supported by
        the node in question and adds it the selected submission_id.

        * Request:
        {'context_1_field':
            {'field_name1': <content>},
            {'field_name2': <content>}
        }

        * Response:
          Status Code: 202 (accepted)

        _ If submission_id is invalid
          Status Code: 204 (No Content)
          { error-code: <Int>, error-message: 'submission ID is invalid' }


`/submission/<submission_id>/add_group`

    :POST
        adds a group to the list of recipients for the selected submission.

        * Request:
        {'groups': [ ID(s) of selected groups ] }

        * Response:
          Status Code: 202 (accepted)

        _ If submission_id is invalid
          Status Code: 204 (No Content)
          { error-code: <Int>, error-message: 'submission ID is invalid' }


`/submission/<submission_id>/finalize`, 

    :POST
        checks if all the 'Required' fields are present, then 
        completes the submission in progress and returns a receipt.

        * Request:
          { 'choosen-Receipt': <String, user selected receipt> }

        * Response:
          If the receipt is fine with the node requisite, and is saved as 
          identificative for the WB Tip, is echoed back to the client
          Status Code: 201 (created)
          { 'Receipt': <String, receipt value> }

        _ If the receipt is expected but is not provided, The submission is
          finalized, and the server create a receipt:
          Status Code: 417 (Expectation Failed)
          { 
            'error-code': <Int>, 
            'error-message': 'Invalid receipt requested',
            'Receipt': <String, receipt value> 
          }

        _ If the field check fail
          Status Code: 406 (Not Acceptable)
          { 'error-code': <Int>, 'error-message': 'fields requirement not respected' }

        _ If submission_id is invalid
          Status Code: 204 (No Content)
          { 'error-code': <Int>, 'error-message': 'submission ID is invalid' }


`/submission/<submission_id>/upload_file`, 

    :GET
        return the status of the file uploaded under submission_id,
        TODO: 
        REMIND:
            supports resume. Check JQuery FileUploader and their REST/protocol
            FileUploader has a dedicated REST interface to handle start|stop|delete.

    :PUT
        attach a file to the selected submission_id.

        * Request:
          {'comment': <string (optional) description of the file>}

        * Response:
          { filename: <string>, comment: <String>, size: <Int, in bytes>, content-type: <string> }
          Status Code: 202 (accepted)

    :DELETE
        * Request:
          { delete_id : <Int, ID of the file to be deleted> }
          Status Code: 202 (accepted)

    :(either PUT & DELETE)
        _ If submission_id is invalid
          Status Code: 204 (No Content)
          { 'error-code': <Int>, error-message: 'submission ID is invalid' }


`/tip/<string t_id>` (shared between Rcvr & Wb)

    :GET
        Permit either to WB authorized by Receipt, or to Receivers.
        Both actors have a single, authorized and univoke "t_id".

        Returns the content of the submission with the specified ID.
        Inside of the request headers, if supported, the password for accessing
        the tip can be passed. This returns a session cookie that is then
        used for all future requests to be authenticated.

        * Response:
          Status Code: 200 (OK)
          { 'fields': [{'name': <string Name of the form element>,
                     'title': <string Label of this element>,
                     'description': <string Long description>,
                     'type': <string text|select|radio>,
                     'content': <string Content of submission>},
                      ...
                      ],
            'comments': [{'name': <string name of the commenter>,
                          'date': <DATE 32 bit time_t>,
                          'comment': <string content of the comment> },]
            'material-sets': [{
                    'id': <string the id of the material set>,
                    'link': <string link to download the material>,
                    'files': [ { filename: <string>, comment: <String>, 
                                size: <Int, in bytes>, content-type: <string> } ], 
                    'desc': <String, Description of the material> }]
            'statistics': [{'name': <string name of the receiver>,
                            'group': <string, group of the receiver>,
                            'downloads': <Int download count>,
                            'views': <Int view count> }]
           }

        _ If t_id is invalid
          Status Code: 204 (No Content)
          { error-code: <Int>, error-message: 'requested Tip ID is expired or invalid' }

    :DELETE
        Used to delete a submission if the users has sufficient priviledges.
        Administrative settings can configure if all or some, receivers or
        WB, can delete the submission. default is False.

        * Response:
          If the user has right permissions:
          Status Code: 200 (OK)

        _ If the user has not permission:
          Status Code: 204 (No Content)


`/tip/<string t_id>/add_comment` (shared between Rcvr & Wb)

    Permit either to WB authorized by Receipt, or to Receivers.
    adds a new comment to the submission.

    :POST
        * Request:
          {'comment': <content_of_the_comment>}

        * Response:
          Status Code: 200 (OK)
        _ Error handling as per `/tip/<string t_id>/`


`/tip/<string t_id>/update_file` (Wb only)

    perform update operations. If a Material Set has been started, the file is appended
    in the same pack. A Material Set is closed when the `finalize_update` is called.

    :GET
        return the unfinalized elements accumulated by the whistleblower. The unfinalized
        material are promoted as 'Set' if the WB do not finalize them before a configurable
        timeout.

        * Request: /
        * Response:
        every object is repeated for every "NOT YET finalized Material Set":
        [ 
          'finalized-material-date': <DATE, 32bit time value>,
          'description': <String, description of the Material Set>,
         { filename: <string>, comment: <String>, size: <Int, in bytes>, content-type: <string> },
         { filename: <string>, comment: <String>, size: <Int, in bytes>, content-type: <string> }
        ]

    :PUT
        Used to append a file to a submission.

        * Request:
          { 'comment': <string, file description> }
          { file upload as per HTTP method }

        * Response:
          Status Code: 202 (Accepted)

        _ If a system error happen:
          Status Code: 409 (Conflict)
          { 'error-code': <Int>, 'error-message' : 'Unexpected IO error' }

    :DELETE

        Used to remove a file not yet finalized.

        * Request:
        { 'filename': <String, file name> }

        * Response:
          Status Code: 202 (Accepted)

     :(GET, PUT, DELETE)
        _ Error handling as per `/tip/<string t_id>/`


`/tip/<string t_id>/finalize_update` (Wb only)

    Used to add description in the Material set not yet completed (optional)
    Used to complete the files upload, completing the Material Set.

    :POST
        * Request:
        { 'description': <String, optional description of the Material Set> },
        { 'finalize': True }

        * Response:
            if files are available to be finalized:
            Status Code: 202 (Accepted)

        _ Error handling as per `/tip/<string t_id>/`


`/tip/<string t_id>/download_material` (Rcvr only)

    used to download the material from the
    submission. Can only be requested if the user is a Receiver and the
    relative download count is < max_downloads.

    :GET
        * Request:
        {'id': <material_set_id>, 'option-format': (encrypt|compressed) }

        * Response:
        Stauts Code: 200 (OK)

        _ Error handling as per `/tip/<string t_id>/`


`/tip/<string t_id>/pertinence` (Rcvr only)

    Optional (shall not be supported by configuration settings)
    express a vote on pertinence of a certain submission.
    This can only be done by a receiver that has not yet voted.

    :POST
        * Request: 
        { 'pertinence-vote': <Bool, True mean +1, False mean -1> }

        * Response:
          Status Code: 202 (Accepted)
        _ Error handling as per `/tip/<string t_id>/`


# Receiver API

`/receiver/<string t_id>/overview`

This interface expose all the receiver related info, require one valid Tip authentication.
This interface returns all the options available for the receiver (notification and delivery)
and contain the require field (empty or compiled)

depends from the node administator choose and delivery/notification extension, the capability
to be configured by the user.

(tmp note: overview is the replacement of the previous release "Bouquet")

    :GET
       * Response:
         Stauts Code: 200 (OK)
         {
             'tip-list': { [ 'tip-token': <T_id>, 'tip-title': <String> ],
                           [ 'tip-token': <T_id>, 'tip-title': <String> ] },
             'notification-method': { <ModuleDataStruct>, <ModuleDataStruct>, ... },
             'delivery-method': { <ModuleDataStruct>, <ModuleDataStruct>, ... },
             'receiver-properties': <RDict>
         }

    :POST
       * Request:
         {
             'notification-method': { <ModuleDataStruct>, <ModuleDataStruct> },
             'delivery-method': { <ModuleDataStruct>, <ModuleDataStruct> }
         }

       * Response:
         Stauts Code: 200 (OK)


    :(GET and POST)
        * Error code:
        _ If t_id is invalid
          Status Code: 204 (No Content)
          { error-code: <Int>, error-message: 'requested Tip ID is expired or invalid' }

# Admin API

`/admin/receivers/`

    :GET
        Returns a json object containing all the receivers information.
        * Response:
            Status Code 200 (OK)
            {
               'groups': [ {'groupName': <String GroupName>,
                            'groupDescription': <String GroupDescription>,
                            'lang': <Array, language supported>,
                            'group-id': <Int> },
                           {'groupName': <String GroupName>,
                            'groupDescription': <String GroupDescription>,
                            'lang': <Array, language supported>,
                            'group-id': <Int> },
                         ]
               'receiver-description': [{
                   'name': <String name>, 'description': <String>, 'receiver-ID' : <Int>,
                     'notification-method': { <ModuleAdminConfig>, <ModuleAdminConfig> },
                     'delivery-method': { <ModuleAdminConfig>, <ModuleAdminConfig> }
                        receiver-properties: <RDict>
                        group-list: [ 
                                  { 'group-id' : <Int>, 'group-name': <String> },
                                  { 'group-id' : <Int>, 'group-name': <String> }
                                ],
                   'last-access': <Timeval>,
                   'creation-time' : <Timeval>,
                   'last-update': <Timeval>,
                   'tip-active': <Int, #counter>
                },
                { ... } ]
             }

     :POST
        set the value in few generic fields related to the receiver. If a field is empty,
        is kept the previous value. ID is required 
        * content:
            {
               'ID' : <Int>, 'PublicName': <String name>, 'description': <String>, 
               'PrivateName': <String>,
               'group-list': <Pickle, list of group ID>
            }
        * Response:
            Status Code 200 (OK)

          if ID is not related to an active receiver:
            Status Code 204 (No Content)

     :PUT
        Adds a new receiver to the list of receivers.
        delivery method and notification method are set with default value,
        they need to be specified by a dedicated interface, due to their
        modular/flexible nature

        (as default, a freshly created receiver, can have id and date, but 
         not yet notification/delivery configured)

        * Request:
            {
             'PublicName': <PublicName>,
             'PrivateName': <PrivateName>,
             'Description': <String>,
             'Groups': <Pickle, list of groups ID>,
              receiver-properties: <RDict>
            }

        * Response:
            {'ID': <num>}
              Status: 201 (Created)

          If a system error happen: 
              Status: 404 (Server Error)

    :DELETE
        Delete a receiver and all the information related to him (stats, Tip)
        * Request:
        {'ID': <num>}

        * Response:
          Status: 200 (Accepted)

`/admin/notification/`
`/admin/delivery/`
`/admin/storage/`

These interface show the available modules for notification, delivery and storage.
The admin can enable them and configure the host dependent options. 
<ModuleAdminConfig> is the datatype defined in the section before this.

    :GET
        * Response:
            { 'notification-method': <ModuleAdminConfig> }
          or
            { 'delivery-method': <ModuleAdminConfig> }
          or
            { 'storage-method': <ModuleAdminConfig> }

        * Response:
          Status: 200 (Accepted)

    :POST
        * Request:
            { 'notification-method': <ModuleAdminConfig> }
          or
            { 'delivery-method': <ModuleAdminConfig> }
          or
            { 'storage-method': <ModuleAdminConfig> }

        * Response:
          Status: 202 (Modified)

`/admin/node`

    :GET
        Returns a json object containing all the information of the node.
        * Response:
            Status Code: 200 (OK)
             {
              'name': <string Name of the initiative>,
              'statistics': <string, general statistics>,
              'node-properties': <NDict>,
              'contexts': [{'context_number': <Int of managed receiver groups>},
                           {'context_1': <String name of group>},
                           {'context_1_field':
                                [1: { 'field_name', 'field_type', 'Required' },
                                #F: { 'field_name', 'field_type', 'Required' }]
                            },
                           {'context_#N': <String name of group>},
                           {'context_#N_field':
                                [1: { 'field_name', 'field_type', 'Required' },
                                #F: { 'field_name', 'field_type', 'Required' }]
                            }]
               'descriptiom': <String, descrption headline>,
               'public_site': <String, public URL of the site, if available>,
               'tor2web': <String, public URL of tor2web trusted entry point, if available>,
               'hidden_service': <String, .onion service, if available>,
               'preference_settings': [ Array, lists of options related in
                                        Tip management, like:
                                        max download available per Material Set,
                                        maximum time for finalize a Material,
                                        whistleblowers can delete
                                        whistleblowers can select groups ]
             }
    :POST
        Changes the node public node configuration settings
        * Request:
            {
              'name': <string Name of the initiative>,
              'statistics': <string, general statistics>,
              'node-properties': <NDict>,
              'contexts': [{'context_number': <Int of managed receiver groups>},
                           {'context_1': <String name of group>},
                           {'context_1_field':
                                [1: { 'field_name', 'field_type', 'Required' },
                                #F: { 'field_name', 'field_type', 'Required' }]
                            },
                           {'context_#N': <String name of group>},
                           {'context_#N_field':
                                [1: { 'field_name', 'field_type', 'Required' },
                                #F: { 'field_name', 'field_type', 'Required' }]
                            }]
               'descriptiom': <String, descrption headline>,
               'public_site': <String, public URL of the site, if available>,
               'tor2web': <String, public URL of tor2web trusted entry point, if available>,
               'hidden_service': <String, .onion service, if available>,
               'preference_settings': [ Array, lists of options related in
                                        Tip management, like:
                                        max download available per Material Set,
                                        maximum time for finalize a Material,
                                        whistleblowers can delete
                                        whistleblowers can select groups ]
             }

        * Response:
          Status: 202 (Accepted)

