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
                                [#F: { 'field_name', 'field_type', 'Required' }]
                           {'context_#N': <String name of group>}],
                           {'context_#N_field': 
                                [1: { 'field_name', 'field_type', 'Required' },
                                [#F: { 'field_name', 'field_type', 'Required' }]
               'descriptiom': <string, descrption headline>,
               'public_site': <string, url>,
               'hidden_service': <string, url.onion>,
             },
        example of a result:
             { 
              'name': "blue meth fighting in alberoque",
              'statistics': <string, general statistics>,
              'properties': [ {'end2end_encryption_enforced': True},
                              {'are_receivers_part_of_the_admin': False},
                              {'anonymity_enforced': True},
                            ]
              'contexts': [{'context_number': 2 },
                               {'context_1': 'Heisenberg saitings'},
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
               'public_site': 'http://figthmeth.net',
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

`/tip/`

    (this happens when no <t_id> is specified)
    :GET
        None
        * Response:
          Status Code: 501 (Not implemented)
    :POST
        This creates an empty submission and returns the ID
        to be used when referencing it as a whistleblower.
        * Response:
          Status code: 201 (Created)

`/tip/<string t_id>`

    :GET
        Returns the content of the submission with the specified
        ID.
        * Response:
          Status Code: 200 (OK)
          {'fields': [{'name': <string Name of the form element>,
                     'title': <string Label of this element>,
                     'description': <string Long description>,
                     'type': <string text|select|radio>,
                     'content': <string Content of submission>},
                      ...
                      ]
           }
    :POST
        Append to a created submission when all the fields have not been
        created.
        * Request:
          {'submissionid': <string The id of the submission obtained from the GET>,
          'fields': <form all the data in the fields>}
        * Response:
          Status Code: 200 (OK)
          If that was the last element required then:
          {'result': 'finished'}
          If still some required content is missing:
          {'result': 'ok'}

    :PUT
        Used to append material to a submission.
        * Request:
          {'description': <string (optional) Description of the material}
        * Response:
          Status Code: 202 (Accepted)

    :DELETE
        Used to delete a submission.
        * Response:
          Status Code: 204 (No Content)

`/tip/<string t_id>/statistics/`

    :GET
        Used to retrieve the statistics for a particular
        submission.
        * Response:
          Status Code: 200 (OK)
          {'0': {'name': <string name of the target>,
                 'downloads': <int download count>,
                 'views': <int view count>
                 },
            '1': ...
            ...
          }
    :POST
        None

`/tip/<string t_id>/comments/?<c_id>`

    :GET
        Used to retrieve the comments for a submission. They
        are ordered from most recent to oldest to newest (0 is
        oldest). The optional c_id value allow to retrieve
        only comments with id >= c_id.
        * Response:
          Status Code: 200 (OK)
          {'0': {'name': <string name of the commenter>,
                 'comment': <string content of the comment>
                },
            '1': ...
            ...
          }
    :POST
        Used to post a comment to the submission.
        * Request:
          {'comment': <string Comment contents>}
        * Response:
          Status Code: 200 (OK)

`/tip/<string t_id>/material/`

    :GET
        Used to retrieve all the list of currently uploaded
        material. They are sorted from oldest to newest (0
        oldest)
        * Response:
          Status Code: 200 (OK)
          {'0': {'id': <string the id of the material>,
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
          }

     :POST
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
        Used to add material to a submission.
        * Request:
          {'name': <string file name>,
           'id': <string (optional) the id of an in progress material submission>,
           'fin': <bool (optional) used to close the material package>,
           'desc': <string (optional) description of the file>
           }
        * Response:
          When a material is not finalized:
          Status Code: 202 (Accepted)

          When it is final
          Status Code: 200 (OK)

# Admin API

`/targets/`

    TODO

`/groups/`

    TODO

`/admin/`

    TODO

`/stats/`

    TODO

