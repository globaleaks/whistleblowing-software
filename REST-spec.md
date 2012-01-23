# Public API

## /info/

    Returns information on the GlobaLeaks node. This includes
    submission paramters and how information should be presented
    by the client side application.

    :GET
        Returns a json object containing all the information of the node.
        * Response:
            Status Code: 200 (OK)
            { 'type': <int type>,
              '0': { 'title': <string Title of this step>
                     'fields': [{'name': <string Name of the form element>,
                                 'title': <string Label of this element>,
                                 'description': <string Long description>,
                                 'type': <string text|files|select|radio>,
                                 'size': <string (optional) length of text field. w=words, c=characters>,
                                 'options': (optional) [[<string Name of select option>,
                                                        <string Label of select option>],
                                                        ...
                                                        ]
                               }],
                      'buttons': {'next': <string Title of the next button>}
                    },
              '1': ...
              ...
            }
        example of a result:
            { 'type' : 2,
              '0' : {'title': 'Help us fight Corruption!',
                     'fields': [{'name': 'tip',
                                 'title': 'Your tip',
                                 'description': 'Explain the issue in less than 3000 chars',
                                  'type': 'text',
                                  'size': '3000c',
                                  }],
                     'buttons': {'next': 'Add some files'}
                    },
              '1' : {'title': 'Load Documents',
                     'fields': [{'name': 'files',
                                 'title': 'select files',
                                 'type': 'files'
                                 },
                                {'name': 'documentDescription',
                                 'title': 'Describe the documents',
                                 'description': 'Explain the content of the \
                                 uploaded material in less than 100 words',
                                  'type': 'text',
                                  'size': '100w',
                                  }
                                ],
                     'buttons': {'next': 'Add more details',
                                 'finish': 'Finalize the submission'}
                     },
              '2' : {'title': '',
                     'fields': [
                                {'name': 'someText1',
                                 'title': 'Some Text',
                                 'description': '',
                                  'type': 'text',
                                  'size': None,
                                  },
                                {'name': 'someText2',
                                 'title': 'Some Text',
                                 'description': '',
                                  'type': 'string',
                                  'size': None
                                  },
                                {'name': 'someText3',
                                 'title': 'Some Text',
                                 'description': '',
                                  'type': 'select',
                                  'options': [
                                              ['Something', 'something'],
                                              ['Something else', 'somethingelse']
                                              ]
                                  },
                                {'name': 'someText4',
                                 'title': 'Some Text',
                                 'description': '',
                                  'type': 'date',
                                  'size': None,
                                  },
                                {'name': 'someText5',
                                 'title': 'Some Text',
                                 'description': '',
                                  'type': 'radio',
                                  'options': [
                                              ['Option 1', 'opt1'],
                                              ['Option 2', 'opt2'],
                                              ['Option 3', 'opt3']
                                              ],
                                  'size': None,
                                  }
                                ]
                     }
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

## /tip/

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

## /tip/<string t_id>

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

    /statistics/
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

    /comments/?<c_id>
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

    /material/
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

## /targets/
TODO

## /groups/
TODO

## /admin/
TODO

## /stats/
TODO

