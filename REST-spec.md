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
        example of a result:
             {
              'name': "blue meth fighting in alberoque",
              'statistics': <string, general statistics>,
              'properties': [ {'end2end_encryption_enforced': True},
                              {'are_receivers_part_of_the_admin': False},
                              {'anonymity_enforced': True},
                            ]
              'contexts': [{'context_number': 2 },
                               {'context_1': 'Heisenberg sightings'},
                               {'context_1_field':
                                    [ { 'headline', 'text', True },
                                      { 'photo', 'img', False },
                                      { 'descriptio', 'text', True }, ]
                               }
                               {'context_2': <String name of group>}],
                               {'context_2_field':
                                    [ { 'headline', 'text', True },
                                      { 'photo', 'img', False },
                                      { 'descriptio', 'text', True }, ]
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

        `/finalize`, completes the submission in progress and
        returns a receipt.

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
        **add_material**, adds material to the selected submission_id.

        * Response:
          Status Code: 202 (accepted)

    :DELETE

`/tip/<string t_id>`

    :GET
        Returns the content of the submission with the specified
        ID.
        Inside of the request headers, if supported, the password for accessing
        the tulip can be passed. This returns a session cookie that is then
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

    :POST
        `/add_comment`, adds a new commnet to the submission.

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

    :PUT
        Used to append material to a submission. This can only be done by the
        whistleblower.

        * Request:
          {'name': <string file name>,
           'id': <string (optional) the id of an in progress material submission>,
           'fin': <bool (optional) used to close the material package>,
           'desc': <string (optional) description of the file>
           }

        * Response:
          Status Code: 202 (Accepted)

    :DELETE
        Used to delete a submission.
        * Response:
          Status Code: 204 (No Content)


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
                                    'security_method': {'type': <type>, 'content': <content>}
                                    },
                 'notificationMethod': {'type': <type>,
                                    'address': <adress>,
                                    'security_method': {'type': <type>, 'content': <content>}
                                    }
                },
           {'ID', <num>, 'PublicName': <PublicName>,
                 'PrivateName': <PrivateName>,
                 'Groups': [<list_of_groups>],
                 'deliveryMethod': {'type': <type>,
                                    'address': <adress>,
                                    'security_method': {'type': <type>, 'content': <content>}
                                    },
                 'notificationMethod': {'type': <type>,
                                    'address': <adress>,
                                    'security_method': {'type': <type>, 'content': <content>}
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
                                'security_method': {'type': <type>, 'content': <content>}
                                },
             'notificationMethod': {'type': <type>,
                                    'address': <adress>,
                                    'security_method': {'type': <type>, 'content': <content>}
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
                                'security_method': {'type': <type>, 'content': <content>}
                                },
             'notificationMethod': {'type': <type>,
                                    'address': <adress>,
                                    'security_method': {'type': <type>, 'content': <content>}
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


