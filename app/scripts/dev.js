// This is a mock HTTP Backend to allow end to end testing (that is testing via
// the browser) and to allow backend-less development of GLClient
//
// It also includes some changes that I would need made to the API.

GLClientDev = angular.module('GLClientDev', ['GLClient', 'ngMockE2E']);
GLClientDev.run(function($httpBackend) {
  var form_fields = [];

  form_fields[0] = [{
    'label': 'Item 1',
    'name': 'item1', 'required': true,
    'type': 'textarea', 'placeholder': 'Enter the Item 1',
    'value': '', 'hint': 'this is the hint for the form'
  },
  {'label': 'Item 2',
    'name': 'item2', 'required': true,
    'type': 'text', 'placeholder': 'Enter the Item 2',
    'value': '', 'hint': 'this is the hint for the form'
  }];

  form_fields[1] = [{
    'label': 'Car 1',
    'name': 'car1', 'required': false,
    'type': 'textarea', 'placeholder': 'Enter the Car 1',
    'value': '', 'hint': 'this is the hint for the form'
  },
  {'label': 'Car 2',
    'name': 'car2', 'required': true,
    'type': 'text', 'placeholder': 'Enter the Car 2',
    'value': '', 'hint': 'this is the hint for the form'
  }];

 
  var receivers = [{"gus": 'r_antanisblinda1',
     "can_delete_submission": true,
     "can_postpone_expiration": true,
     "can_configure_notification": true,
     "can_configure_delivery": true,
     "can_trigger_escalation": false,
     "receiver_level": 1,
     "name": "Beppe Scamozza",
     "description": "A local activist",
     "tags": "activism,local",

     "creation_date": 123467898765,
     "last_update_date": 12345678922,
     "languages_supported": ['en', 'it'],
    },
    {"gus": 'r_antanisblinda2',
     "can_delete_submission": false,
     "can_postpone_expiration": false,
     "can_configure_notification": false,
     "can_configure_delivery": false,
     "can_trigger_escalation": false,
     "receiver_level": 1,
     "name": "Pasquale Achille",
     "description": "A famous journalist",
     "tags": "journalism",

     "creation_date": 123567890,
     "last_update_date": 123345678,
     "languages_supported": ['en', 'it'],
    }]

  var node_info = {
    'name': {'en': 'Some Node Name', 
      'it': 'Il nome del nodo'},

    'statistics': {'active_contexts': 2,
      'active_receivers': 2,
      'uptime_days': 10
    },
    'contexts': [{
        'gus': "1",
        'name':
          {'en': 'Context Name 1',
            'it': 'Nome Contesto 1'
          },
        'description': {'en': 'Context description 2',
          'it': 'Descrizione contesto 2'
        },
        'creation_date': 1353060996,
        'update_date': 1353060996,
        'fields': form_fields[0],
        'receivers': receivers
      },
      {
        'gus': "2",
        'name':
          {'en': 'Context Name 2',
            'it': 'Nome Contesto 2'
          },
        'description': {'en': 'Context description 2',
          'it': 'Descrizione contesto 2'
        },
        'creation_date': 1353060996,
        'update_date': 1353060996,
        'fields': form_fields[1],
        'receivers': receivers
      }
    ],
    'node_properties': {'anonymous_submission_only': true},
    'public_site': 'http://example.com/',
    'hidden_service': 'httpo://example.onion',
  }

  // returns the node information
  $httpBackend.whenGET('/node').respond(node_info);

  $httpBackend.whenPOST('/submission/new')
    .respond(function(method, url, data){
      // This interface is used both for the creation of a new submission 
      // The major changes with the previous API are:
      //
      // * The context_id is not passed as a URL parameter but in the body of
      //   the request.
      //
      // * The returned value of this has changed quite a bit.
      //
      // For details on what should be in the response see the response section.

      var context_gus = data['context_gus'],
          selected_context = {},
          context_fields = {},
          context_receivers = [];

      for (context in node_info.contexts) {
        if (context_gus == context.gus) {
          selected_context = context;
          break;
        }
      }

      for (field in selected_context.fields) {
        context_fields[field.name] = '';
      }

      for (receiver in selected_context.receivers) {
        context_receivers.push(receiver.gus);
      }

      response = {
        'submission_gus': 's_antanisblinda',
        'fields': context_fields,
        'receivers_selected': context_receivers,
        'context_gus': context_gus,
        'folder_name': '',
        'folder_description': ''
      }

      console.log("writing this response");
      console.log(response);

      return [200, response];
  });

  $httpBackend.whenPOST('/submission/')
    .respond(function(method, url, data){
      // This interface is used to conclude a submission in progress. 
      // Here we will do checks if all the required preconditions are satisfied
      // and if they are we will return what the client has requested plus the
      // submission receipt.

      var response = data;
      if (!data['submission_receipt']) {
        response['submission_receipt'] = 'somerandomstring';
      }

      return [200, response];
  });

  // XXX this is not implemented for the moment.
  // We need to invert the order of the parameters to make it uniform with the rest of the API.
  //$httpBackend.whenPOST('/submission/files/<submission_id>');
  
  $httpBackend.whenGET(/^views\//).passThrough();
  

});
