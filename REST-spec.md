# Summary

This is a breif summary of the REST API specification.

## Public API

`/node/`

Returns information on the GlobaLeaks node. This includes
submission paramters and how information should be presented
by the client side application.

`/submission`

This creates an empty submission and returns the ID
to be used when referencing it as a whistleblower.
ID is a random 64bit integer.

`/submission/<submission_id>`

Returns the currently submitted fields and material filenames and size.

`/submission/<submission_id>/submit_fields`

does the submission of the fields that are supported by
the node in question and update the selected submission_id

`/submission/<submission_id>/add_group`

adds a group to the list of recipients for the selected
submission. group are addressed by their ID.

`/submission/<submission_id>/finalize`

completes the submission in progress and
returns a receipt.

`/submission/<submission_id>/upload_file`

upload a file to the selected submission_id.

`/tip/<string t_id>`

Returns the content of the submission with the specified ID.
Inside of the request headers, if supported, the password for accessing
the tip can be passed. This returns a session token that is then
used for all future requests to be authenticated.

`/tip/<string t_id>/download_material`

used to download the material from the
submission. Can only be requested if the user is a Receiver and the
relative download count is < max_downloads

`/tip/<string t_id>/add_comment`

adds a new comment to the submission

`/tip/<string t_id>/pertinence`

express a vote on pertinence of a certain submission.
This can only be done by a receiver that has not yet voted.

`/tip/<string t_id>/add_description`

Used to add a description to an already uploaded material. Only the WB
authenticated by their Receipt can do it.

`/tip/<string t_id>/`

Used to add a description to an already uploaded material. Only the WB
authenticated by their Receipt can do it.


## Admin API

`/admin/receivers/`

Interact with the current receivers list.

`/admin/config/node`

For configuring the public details of the node.

`/admin/config/delivery`

For setting up delivery and notification methods.

`/admin/config/storage`

For setting up storage methods.

# Public API

## Under writting!

## Open GLBackend/docs/specification/GLBackend-18-5-2012.png

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
              'name': <string Name of the initiative>,
              'statistics': <string, general statistics>,
              'properties': [ array, lists of node Yes:No selection,
                              describing chooses in Backend setup.
                              Info can be used by LeakDirectory or other
                              external aggregator of nodes.
                            ]
              'contexts': [
                           {'name': <String name of context>,
                            'groups': [ { 'group_ID' : 'group_name' }, { ... } ]
                            'fields': [ 
                                  { 'name' : <string field_name>, type: (txt|int|img), 'Required': <Bool> },
                                  { 'name' : <string field_name>, type: (txt|int|img), 'Required': <Bool> },
                                ]
                            }]
               'descriptiom': <string, descrption headline>,
               'public_site': <string, url>,
               'hidden_service': <string, url.onion>,
             }
        example of a result:
             {
              'name': "blue meth fighting in alberoque",
              'statistics': <string, general statistics>,
              'properties': [ {'end2end_encryption_enforced': True},
                              {'are_receivers_part_of_the_admin': False},
                              {'anonymity_enforced': True},
                            ]
              'contexts': [ 
                            { 'name' : 'Heisenberg sightings',
                              'groups' : [ { 0 : 'police' , 1 : 'vigilantes', 2 : 'Cartel', 3: 'Rihab' } ]
                              'fields': [ { 'name': 'headline', 'type':'text', 'Required': True },
                                          { 'name': 'photo', 'type':'img', 'Required':False },
                                          { 'name': 'description', 'type': 'txt', 'Required':True }, ]
                             },
                             { 'name': 'Milan EXPO 2015'],
                               'groups': [ { 0 : 'police' , 1 : 'journalists', 2 : 'Municipality'} ]
                               'fields': [ { 'headline', 'text', True },
                                           { 'description', 'txt', True },
                                           { 'proof', 'file', True }, ]
                             }
                           ]
               'descriptiom': 'This node aggregate expert of the civil society in fighting the crystal meth, producted by the infamous Heisenberg',
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
        * Response:
          Status code: 201 (Created)

`/submission/<submission_id>`

    :GET
        Returns the currently submitted fields and material filenames and size
        * Response:
          Status Code: 200

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

        `/add_group`, adds a group to the list of recipients for the selected
        submission.

        * Request:
        {'groups': [<list_of_groups>]}

        * Response:
          Status Code: 202 (accepted)

        `/finalize`, checks if all the 'Required' fields are present, then 
        completes the submission in progress and returns a receipt.

        * Request:
        (optional) It supports inline submission of submission fields, to avoid
        doing two separate requests for finalization and fields sending.

        {'context_1_field':
            {'field_name1': <content>},
            {'field_name2': <content>}
        }

        * Response:
          Status Code: 201 (created)

    :PUT
        **upload_file**, attach a file to the selected submission_id.

        * Request:
        {'desc': <string (optional) description of the file>}}

        * Response:
        {'name': <string, name of the uploaded file>, 'id': <Int, associated file ID>}
          Status Code: 202 (accepted)

    :DELETE
        * Request:
        { delete_id : <Int, ID of the file to be deleted> }
          Status Code: 202 (accepted)

`/tip/<string t_id>`

    :GET
        Permit either to WB authorized by Receipt, or to Receivers,
        authorized by univoke "t_id".
        
        Returns the content of the submission with the specified ID.
        Inside of the request headers, if supported, the password for accessing
        the tip can be passed. This returns a session cookie that is then
        used for all future requests to be authenticated.

        * Response:
          Status Code: 200 (OK)
          {'fields': [{'name': <string Name of the form element>,
                     'title': <string Label of this element>,
                     'description': <string Long description>,
                     'type': <string text|select|radio>,
                     'content': <string Content of submission>},
                      ...
                      ],
            'comments': {'0': {'name': <string name of the commenter>,
                              'comment': <string content of the comment>
                              },
                         '1': ...
                              ...
                        },
            'material': {'0': {'id': <string the id of the material>,
                 'link': <string link to download the material>,
                 'files': [{'id': <string id of the file>,
                            'name': <string file name>,
                            'size': <string file size>,
                            'desc': <string (optional) description of the file>},
                            ...
                          ],
                 'desc': <string (optional) Description of the material>
                 },
                ...
                      },
            'statistics': {'0': {'name': <string name of the target>,
                                 'downloads': <int download count>,
                                 'views': <int view count>
                                },
                           '1': ...
                                ...
                          }
           }

           `/download_material`, used to download the material from the
           submission. Can only be requested if the user is a Receiver and the
           relative download count is < max_downloads.

           * Request:
           {'id': <material_id>}
           
          * Response:
            TODO - a lots of incongruence need to be handled here
            TODO - A LOTS OF INCONGRUENCE NEED TO BE HANDLED HERE
           Stauts Code: 200 (OK)

    :POST
        `/add_comment`, adds a new comment to the submission.

        * Request:
          {'comment': <content_of_the_comment>}

        * Response:
          Status Code: 200 (OK)

        `/pertinence`, express a vote on pertinence of a certain submission.
        This can only be done by a receiver that has not yet voted.

        * Response:
          Status Code: 202 (Accepted)

        `/add_description`
        Used to add a description to an already uploaded material.
        * Request:
          {'id': <string the id of the material>,
           'desc': <string content of the description>,
           'fid': <string (optional) the id of the file>
          }
        * Response:
          Status Code: 200 (OK)
          If file or material already has a description:
          Status Code: 304 (Not Modified)

    :DELETE
        Used to delete a submission if the receiver has sufficient priviledges.
        * Response:
          Status Code: 204 (No Content)


`/tip/<string t_id>/material`

    Query the material available, and perform update operations

    :GET
        Permitted to Receivers and WB, return list of 'material packages' available
        
        * Request: /
        * Response:
        every object is repeated for every "finalized group of files":
        [ 
          'finalized-material-date': <DATE, 32bit time value>,
          { name: <string, filename>, size: <Int, expressed in bytes>, content-type: <string, ct> }
          { name: <string, filename>, size: <Int, expressed in bytes>, content-type: <string, ct> }
        ]
        
    :POST
        Permitted to WB only, finalize the currently not finalized uploads performed 
        by PUT.
        
        * Request:
        { 'finalize': True }
        
        * Response:
        
        if files are available to be finalized:
            Status Code: 202 (Accepted)
        else
            Status Code: 204 (No Content)

    :PUT
        Permitted only to the WB.
        Used to append a file to a submission.

        * Request:
          {'name': <string file name>,
           'id': <string (optional) the id of an in progress material submission>,
           'fin': <bool (optional) used to close the material package>,
           'desc': <string (optional) description of the file>
           }

        * Response:
          Status Code: 202 (Accepted)


# Admin API

`/admin/receivers/`

    :GET
        Returns the current receivers list.

        * Response:
          Status Code: 200 (OK)

          {'groups': [{'groupName': <GroupName>,
                       'groupDescription': <GroupDescription>},
                      {'groupName': <GroupName>,
                       'groupDescription': <GroupDescription>}
                      ]

           'receivers': [{'ID': <num>, 'PublicName': <PublicName>,
                 'PrivateName': <PrivateName>,
                 'Groups': [<list_of_groups>],
                 'deliveryMethod': {'type': <type>,
                                    'address': <adress>,
                                    'auth_method': [{'type': <type>,
                                                     'content': <content>}]
                                    },
                                    {'type': 'local',
                                     'address': None,
                                     'auth_method': [{'type': 'password',
                                                      'content': 'antani'}]
                                     'enc_method': [{'type': 'pgp',
                                                     'content': <public_pgp_key>}]
                                    },
                 'notificationMethod': {'type': <type>,
                                    'address': <adress>,
                                    'enc_method': {'type': <type>, 'content': <content>}
                                    }
                },
           {'ID', <num>, 'PublicName': <PublicName>,
                 'PrivateName': <PrivateName>,
                 'Groups': [<list_of_groups>],
                 'deliveryMethod': {'type': <type>,
                                    'address': <adress>,
                                    'auth_method': [{'type': <type>,
                                                     'content': <content>}],
                                    'enc_method': [{'type': <type>,
                                                    'content': <content>}]
                                    },
                 'notificationMethod': {'type': <type>,
                                    'address': <adress>,
                                    'enc_method': {'type': <type>, 'content': <content>}
                                    }
                }
            ]
          }

    :POST
        Adds a new receiver to the list of receivers.

        * Request:

            {'PublicName': <PublicName>,
             'PrivateName': <PrivateName>,
             'Groups': [<groupA>, <groupB>]
             'deliveryMethod': {'type': <type>,
                                'address': <adress>,

                                'auth_method': [{'type': <type>,
                                                 'content': <content>}],
                                'enc_method': [{'type': <type>,
                                                'content': <content>}]
                                },
             'notificationMethod': {'type': <type>,
                                    'address': <adress>,
                                    'enc_method': {'type': <type>, 'content': <content>}
                                    }
            }

        * Response:
          Status: 201 (Created)

        `/edit_receiver`

        * Request:

        {'PublicName': <PublicName>,
             'PrivateName': <PrivateName>,
             'Groups': [<groupA>, <groupB>]
             'deliveryMethod': {'type': <type>,
                                'address': <adress>,

                                'auth_method': [{'type': <type>,
                                                 'content': <content>}],
                                'enc_method': [{'type': <type>,
                                                'content': <content>}]
                                },
             'notificationMethod': {'type': <type>,
                                    'address': <adress>,
                                    'enc_method': {'type': <type>, 'content': <content>}
                                    }
        }

        * Response:
          Status: 202 (Modified)

    :DELETE

        * Request:
        {'ID': <num>}

        * Response:
          Status: 202 (Accepted)

`/admin/config/node`

    :GET
        Returns a json object containing all the information of the node.
        * Response:
            Status Code: 200 (OK)
             {
              'name': <string Name of the initiative>,
              'statistics': <string, general statistics>,
              'properties': [ array, lists of node Yes:No selection,
                              describing chooses in Backend setup.
                              Info can be used by LeakDirectory or other
                              external aggregator of nodes.
                            ]
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
               'descriptiom': <string, descrption headline>,
               'public_site': <string, url>,
               'hidden_service': <string, url.onion>,
             }
    :POST
        Changes the node public node configuration settings
        * Request:
            {
              'name': <string Name of the initiative>,
              'statistics': <string, general statistics>,
              'properties': [ array, lists of node Yes:No selection,
                              describing chooses in Backend setup.
                              Info can be used by LeakDirectory or other
                              external aggregator of nodes.
                            ]
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
               'descriptiom': <string, descrption headline>,
               'public_site': <string, url>,
               'hidden_service': <string, url.onion>,
             }

        * Response:
          Status: 202 (Accepted)

`/admin/config/delivery`

    :GET
    Returns the currently installe delivery and notification modules.

    * Response:

    {'delivery_modules': [{'type': 'email', 'settings':
                                            {'smtp_server': <address>,
                                             'user_name': <username>,
                                             'password': <password>,
                                             'ssl': <bool>,
                                            }
                          {'type': <type_name>, 'settings': {}}
                          ]
     'notification_modules': [{'type': 'email', 'settings':
                                            {'smtp_server': <address>,
                                             'user_name': <username>,
                                             'password': <password>,
                                             'ssl': <bool>,
                                            }
                          {'type': <type_name>, 'settings': {}}
                          ]
    }


    :POST
    Update the currently configured delivery and notification modules.


    * Request:
    {'delivery_modules': [{'type': 'email', 'settings':
                                            {'smtp_server': <address>,
                                             'user_name': <username>,
                                             'password': <password>,
                                             'ssl': <bool>,
                                            }
                          {'type': <type_name>, 'settings': {}}
                          ]
     'notification_modules': [{'type': 'email', 'settings':
                                            {'smtp_server': <address>,
                                             'user_name': <username>,
                                             'password': <password>,
                                             'ssl': <bool>,
                                            }
                          {'type': <type_name>, 'settings': {}}
                          ]
    }

    * Response
    Status Code: 202 (Accepted)


`/admin/config/storage`

    :GET
    Returns the currently installed storage methods

    * Response:

    {'storage_modules': [{'type': 'ftp', 'settings':
                                            {'ftp_server': <address>,
                                             'user_name': <username>,
                                             'password': <password>,
                                             'ssl': <bool>,
                                            },
                          {'type': 'scp', 'settings':
                                            {'scp_server': <address>,
                                             'user_name': <username>,
                                             'private_key': <private_key>,
                                             'password': <password>,
                                             'ssl': <bool>,
                                            },
                           },
                           {'type': 'mysql', 'settings':
                                            {'mysql_server': <address>,
                                             'user_name': <username>,
                                             'database': <database_name>,
                                             'password': <password>,
                                            },
                          },
                          {'type': 'local', 'settings': {'path': <path>}},
                          {'type': <type_name>, 'settings': {}}
                          ]
     }


    :POST
    Update the currently configured storage modules.

    * Request:
    {'storage_modules': [{'type': 'ftp', 'settings':
                                            {'ftp_server': <address>,
                                             'user_name': <username>,
                                             'password': <password>,
                                             'ssl': <bool>,
                                            }
                          {'type': <type_name>, 'settings': {}}
                          ]
     }

    * Response
    Status Code: 202 (Accepted)


