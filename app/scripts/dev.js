// This is a mock HTTP Backend to allow end to end testing (that is testing via
// the browser) and to allow backend-less development of GLClient
//
// It also includes some changes that I would need made to the API.

GLClientDev = angular.module('GLClientDev',
    ['GLClient', 'ngMockE2E']);
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
     "languages_supported": ['en', 'it']
    }];

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
        'description': {'en': 'Context description 1',
          'it': 'Descrizione contesto 1'
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
    'available_languages': [{'code': 'en',
       'name': 'English'}, {'name': 'Italiano',
       'code': 'it'}]
  }

  var create_submission = function(data) {
    var context_gus = data['context_gus'],
        selected_context = {},
        context_fields = {},
        context_receivers = [];

    for (i in node_info.contexts) {
      console.log(node_info.contexts[i]);
      console.log(context_gus);
      if (context_gus == node_info.contexts[i].gus) {
        selected_context = node_info.contexts[i];
        break;
      }
    }

    for (i in selected_context.fields) {
      var field = selected_context.fields[i];
      context_fields[field.name] = '';
    }

    for (i in selected_context.receivers) {
      var receiver = selected_context.receivers[i];
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
    return response;
  }

  /******************/
  /** Node Handler **/
  /******************/
  // * /node U1
  // returns the node information
  $httpBackend.whenGET('/node').respond(node_info);

  /*************************/
  /** Submission Handlers **/
  /*************************/
  $httpBackend.whenPOST('/submission')
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
      //
      // Request payload will be if creating a submission:
      //
      // {
      //   'context_gus': context_gus,
      // }
      //
      // If you are updating a submission:
      // {
      //   'context_gus': context_gus,
      //   'submission_gus': 's_antanisblinda',
      //   'fields': context_fields,
      //   'receivers_selected': context_receivers,
      //   'folder_name': '',
      //   'folder_description': ''
      // }
      //
      // Response the values that have been stored in the database + the gus:
      //
      // {
      //   'context_gus': context_gus,
      //   'submission_gus': 's_antanisblinda',
      //   'fields': context_fields,
      //   'receivers_selected': context_receivers,
      //   'folder_name': '',
      //   'folder_description': ''
      // }

      var data = JSON.parse(data),
          response;

      if (!data['submission_gus']) {
        response = create_submission(data);
      } else if (!data['submission_receipt']) {
        console.log("did not get a proposed receipt");
        response = data;
        response['submission_receipt'] = 'somerandomstring';
      } else {
        console.log("got a proposed receipt");
        response = data;
      }
      response = JSON.stringify(response);
      console.log(response);

      return [200, response];
  });

  /** /file U4 **/
  /** XXX if this is on a separate line perhaps rename it to /upload? **/
  $httpBackend.whenGET('/file').
    respond(function(method, url, data){
  });

  /** /statistics U4 **/
  $httpBackend.whenGET('/statistics').
    respond(function(method, url, data){
  });

  /******************/
  /** Tip Handlers **/
  /******************/

  // /tip/<tip_GUS>/ T1
  // XXX this is not implemented for the moment.
  // We need to invert the order of the parameters to make it uniform with the rest of the API.
  //$httpBackend.whenPOST('/submission/files/<submission_id>');

  $httpBackend.whenGET(/\/tip\/(.*)/).respond(function(method, url, data){
    var tip_description_dict = {
      'id' : '12345',
      // Why do we have the name also?
      'context_gus' : ['Antani Name', 'c_testingit' ],
      'creation_date' : '1353312789',
      'expiration_date' : '1353314789',
      'fields' : [{'label': 'Item 2',
        'name': 'item2',
        'required': true,
        'type': 'text',
        'value': 'Item 2 value',
        'hint': 'this is the hint for the form'
      }],
      'download_limit' : 100,
      'access_limit' : 20,
      'mark' : 0,
      'pertinence' : 10,
      'escalation_treshold' : 10,
      'receiver_map' : [{
        'receiver_gus': 'r_antanisblinda',
        'receiver_level': 1,
        // XXX what is the purpose of this?
        'tip_gus': 't_helloworld',
        'notification_selected': 'email',
        // XXX what is this?
        'notification_fields': 'XXXX'
      },
      {'receiver_gus': 'r_antanisblinda',
        'receiver_level': 1,
        // XXX what is the purpose of this?
        'tip_gus': 't_helloworld',
        'notification_selected': 'email',
        // XXX what is this?
        'notification_fields': 'XXXX'
      }]
    }
    console.log(method);
    console.log(url);
    console.log(data);
    return [200, description_dict];
  });

  // XXX Are these implemented in GLB?
  $httpBackend.whenGET('/\/tip\/(.*)\/comments/').respond(function(method, url, data){
    console.log(method);
    console.log(url);
    console.log(data);
  });

  // XXX Are these implemented in GLB?
  $httpBackend.whenPOST('/\/tip\/(.*)\/comments/').respond(function(method, url, data){
    console.log(method);
    console.log(url);
    console.log(data);
  });

  // * /tips/<tip_GUS> T2
  $httpBackend.whenGET(/\/tips\/(.*)/).
    respond(function(method, url, data){
    console.log(method);
    console.log(url);
    console.log(data);
  });

  /***********************/
  /** Receiver Handlers **/
  /***********************/

  // * /reciever/<receiver_token_auth>/management R1
  //
  $httpBackend.whenGET(/\/receiver\/(.*)\/management/).
    respond(function(method, url, data){
    console.log(method);
    console.log(url);
    console.log(data);
  });

  // * /receiver/<receiver_token_auth>/management R2
  $httpBackend.whenGET(/\/receiver\/(.*)\/management/).
    respond(function(method, url, data){
    console.log(method);
    console.log(url);
    console.log(data);

  });

  // XXX is this profiles or pluginprofiles?
  // * /receiver/<receiver_token_auth>/profiles R2
  $httpBackend.whenGET(/\/receiver\/(.*)\/pluginprofiles/).
    respond(function(method, url, data){
    console.log(method);
    console.log(url);
    console.log(data);
  });

  // XXX is this settings or plugin?
  // I think settings.
  // * /receiver/<receiver_token_auth>/settings R3
  $httpBackend.whenGET(/\/receiver\/(.*)\/settings/).
    respond(function(method, url, data){
    console.log(method);
    console.log(url);
    console.log(data);

  });
  /********************/
  /** Admin Handlers **/
  /********************/

  // * /admin/node A1
  $httpBackend.whenGET('/admin/node').
    respond(function(method, url, data){
    var response = {
      'admin_email': 'admin@example.com',
      'keywords': 'keyword1, keyword2, keyword3',
      'description': {'en': 'Node Description English',
            'it': 'Descrizione nodo italiano'
        },
      'name': {'en': 'Node name english',
        'it': 'Nome nodo italiano'
        },
      'supported_languages': {'en': 'English',
        'it': 'Italiano', 'sr': 'Serbian'},
      'enabled_languages': {'en': true, 'sr': false, 'it': true},
      'default_language': 'it'
    };

    return [200, response];
  });

  $httpBackend.whenPOST('/admin/node').
    respond(function(method, url, data){
    console.log("saving node data");
    console.log(data);
    return [200, data];
  });

  // * /admin/contexts A2
  $httpBackend.whenGET('/admin/contexts').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  $httpBackend.whenPOST('/admin/contexts').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  // * /admin/context A3
  $httpBackend.whenGET('/admin/context').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  $httpBackend.whenPOST('/admin/context').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  // * /admin/receivers A4
  $httpBackend.whenGET('/admin/receivers').
    respond(function(method, url, data){
    function receiver(){
      return {
      'gus': 'r_receivergus1',
      'can_delete_submission': true,
      'can_postpone_expiration': true,
      'can_configure_notification': true,
      'can_configure_delivery': true,
      'can_trigger_escalation': true,
      'level': 1,
      'name': 'Beppe',
      'description': 'This is an activist',
      'tags': 'activism, something',
      'creation_date': '1353312789',
      'last_update_time': '1353312789',
      'languages_supported': ['en', 'it'],
      'notification_address': 'beppe@example.com'
      }
    };

    var response = [];
    for (var i = 0;i <= 10;i++) {
      var r_copy = new receiver;
      r_copy.name += i;
      r_copy.notification_address += i;
      response.push(r_copy);
    }
    return [200, response];
  });

  $httpBackend.whenPOST('/admin/receivers').respond(function(method, url, data){
    console.log(method);
    console.log(url);
    console.log(data);
  });

  // * /admin/receiver A5
  $httpBackend.whenGET('/admin/receiver').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  $httpBackend.whenPOST('/admin/receiver').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  // * /admin/plugins A6
  $httpBackend.whenGET('/admin/plugins').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  $httpBackend.whenPOST('/admin/plugins').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  // * /admin/profile A7
  $httpBackend.whenGET('/admin/profile').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  $httpBackend.whenPOST('/admin/profile').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  // * /admin/statistics A8
  $httpBackend.whenGET('/admin/statistics').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  $httpBackend.whenPOST('/admin/statistics').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  // * /admin/overview A9
  $httpBackend.whenGET('/admin/overview').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  $httpBackend.whenPOST('/admin/overview').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  // * /admin/tasks/ AA
  $httpBackend.whenGET('/admin/tasks').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });

  $httpBackend.whenPOST('/admin/tasks').
    respond(function(method, url, data){
    var response = {};
    return [200, response];
  });


  $httpBackend.whenGET(/^views\//).passThrough();

});
