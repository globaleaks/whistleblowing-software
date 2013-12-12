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
  },
  {'label': 'Item 2',
    'name': 'item2', 'required': true,
    'type': 'text', 'placeholder': 'Enter the Item 2',
    'value': '', 'hint': 'this is the hint for the form'
  },
  {'label': 'Item 3',
    'name': 'item3', 'required': false,
    'type': 'text', 'placeholder': 'Enter the Item 2',
    'value': '', 'hint': 'this is the hint for the form'
  },
  {'label': 'Item 3',
    'name': 'item3', 'required': false,
    'type': 'text', 'placeholder': 'Enter the Item 2',
    'value': '', 'hint': 'this is the hint for the form'
  },
  {'label': 'Item 4',
    'name': 'item4', 'required': false,
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

  var receivers = [{
    "can_configure_delivery": true,
    "can_configure_notification": true,
    "can_delete_submission": true,
    "can_postpone_expiration": true,
    "contexts": [
      "c_IZLJpOxNSXeuMQnuLZCm"
    ],
    "creation_date": "Wed Feb  6 09:18:59 2013",
    "description": "An Example Receiver",
    "languages": [
      "en",
      "it"
    ],
    "name": "An Example Receiver",
    "receiver_gus": "r_bJgDoEilpvJxydvrzOoa",
    "receiver_level": 1,
    "tags": [],
    "update_date": "Wed Feb  6 09:19:21 2013"
  },
  {
    "can_configure_delivery": true,
    "can_configure_notification": true,
    "can_delete_submission": true,
    "can_postpone_expiration": true,
    "contexts": [
      "c_IZLJpOxNSXeuMQnuLZCm"
    ],
    "creation_date": "Wed Feb  6 09:19:25 2013",
    "description": "An Example Receiver 2",
    "languages": [
      "en",
      "it"
    ],
    "name": "An Example Receiver 2",
    "receiver_gus": "r_scIBPjjSnUUcINIaflTl",
    "receiver_level": 1,
    "tags": [],
    "update_date": "Wed Feb  6 09:19:32 2013"
  }];

  var contexts = [{
    "context_gus": "c_IZLJpOxNSXeuMQnuLZCm",
    "description": "This is the an example context description",
    "escalation_threshold": null,
    "fields": form_fields[0],
    "file_max_download": 42,
    "languages": [],
    "name": "An Example Context",
    "receivers": [
      "r_bJgDoEilpvJxydvrzOoa"
    ],
    "selectable_receiver": true,
    "tip_max_access": 42,
    "tip_timetolive": 42,
    "submission_timetolive": 42
  },
  {
    "context_gus": "c_IZLJpOxNSXeuMQnuLZC2",
    "description": "This is the an example context description 2",
    "escalation_threshold": null,
    "fields": form_fields[0],
    "file_max_download": 42,
    "languages": [],
    "name": "An Example Context 2",
    "receivers": [
      "r_bJgDoEilpvJxydvrzOoa"
    ],
    "selectable_receiver": true,
    "tip_max_access": 42,
    "tip_timetolive": 42,
    "submission_timetolive": 42
  }];

  var node = {
      "description": "Please, set me: description",
      "email": "email@dumnmy.net",
      "hidden_service": "Please, set me: hidden service",
      "languages": [
        {'code': 'it', 'name': 'Italiano'},
        {'code': 'en', 'name': 'English'}
      ],
      "name": "Please, set me: name/title",
      "public_site": "Please, set me: public site",
      "stats_update_time": 2
    };

  var comment_description_dict = {
    'comment_id' : 1,
    'source' : 'receiver', //receiver, wb, system
    'content' : 'Lorem Ipsum',
    'author' : 'Beppe',
    'notification_mark': 'not notified', // u'not notified',
          // u'notified', u'unable to notify', u'notification ignored'

    // XXX is this returned by GLB?
    'internaltip_id' : 'foobar',
    // XXX we may want to change this to seconds since epoch in UTC
    // this involves just doing a grep -rn "prettyDateTime" globaleaks/
    // and replacing it with "utcTimeNow"
    // We probably want to change "utcTimeNow" to return an int instead of a
    // float.
    'creation_time' : 1355236662
  };

  var create_submission = function(data) {
    var context_gus = data['context_gus'],
        selected_context = {},
        context_fields = {},
        context_receivers = [];

    for (i in node.contexts) {
      console.log(node.contexts[i]);
      console.log(context_gus);
      if (context_gus == node.contexts[i].gus) {
        selected_context = node.contexts[i];
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
      'receivers': context_receivers,
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
  $httpBackend.whenGET('/node').respond(node);

  // * /contexts
  $httpBackend.whenGET('/contexts').respond(contexts);

  // * /receivers
  $httpBackend.whenGET('/receivers').respond(receivers);

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

  $httpBackend.whenPUT(/\/submission\/(.*)/)
    .respond(function(method, url, data){
      // This allows to add data to a created submission.
      // The key used is the submission id
      //
      // If you are updating a submission:
      // {
      //   'context_gus': context_gus,
      //   'submission_gus': 's_antanisblinda',
      //   'fields': context_fields,
      //   'receivers': context_receivers,
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
      //   'receivers': context_receivers,
      //   'folder_name': '',
      //   'folder_description': ''
      // }


      var data = JSON.parse(data),
        response;

      if (!data['submission_gus']) {
        response = create_submission(data);
      } else if (!data['receipt']) {
        response = data;
        response['receipt'] = 'somerandomstring';
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


  $httpBackend.whenGET(/\/tip\/(.*)\/receivers/).
    respond(function(method, url, data){
    var tip_receivers_resource = [{
        "can_configure_delivery": true,
        "can_configure_notification": true,
        "can_delete_submission": true,
        "can_postpone_expiration": true,
        "contexts": [
            "c_IZLJpOxNSXeuMQnuLZCm"
        ],
        "creation_date": "Wed Feb  6 09:18:59 2013",
        "description": "An Example Receiver",
        "languages": [
            "en",
            "it"
        ],
        "name": "An Example Receiver",
        "receiver_gus": "r_bJgDoEilpvJxydvrzOoa",
        "receiver_level": 1,
        "tags": [],
        "update_date": "Wed Feb  6 09:19:21 2013"
    },
    {
        "can_configure_delivery": true,
        "can_configure_notification": true,
        "can_delete_submission": true,
        "can_postpone_expiration": true,
        "contexts": [
            "c_IZLJpOxNSXeuMQnuLZCm"
        ],
        "creation_date": "Wed Feb  6 09:19:25 2013",
        "description": "An Example Receiver 2",
        "languages": [
            "en",
            "it"
        ],
        "name": "An Example Receiver 2",
        "receiver_gus": "r_scIBPjjSnUUcINIaflTl",
        "receiver_level": 1,
        "tags": [],
        "update_date": "Wed Feb  6 09:35:23 2013"
    },
    {
        "can_configure_delivery": true,
        "can_configure_notification": true,
        "can_delete_submission": true,
        "can_postpone_expiration": true,
        "contexts": [
            "c_IZLJpOxNSXeuMQnuLZCm"
        ],
        "creation_date": "Wed Feb  6 09:19:25 2013",
        "description": "An Example Receiver 2",
        "languages": [
            "en",
            "it"
        ],
        "name": "An Example Receiver 3",
        "receiver_gus": "r_scIBPjjSnUUcINIaflTl",
        "receiver_level": 1,
        "tags": [],
        "update_date": "Wed Feb  6 09:35:23 2013"
    }];

    return [200, tip_receivers_resource];
  });

  $httpBackend.whenGET(/\/tip\/(.*)\/comments/).
    respond(function(method, url, data){
    var tip_comments_resource = [{
      "author_gus": "None",
      "comment_id": "1",
      "content": "asdasdsda",
      "creation_time": "Wed Feb  6 09:39:30 2013",
      "internaltip_id": 1,
      "notification_mark": true,
      "source": "whistleblower"
    }];

    return [200, tip_comments_resource];
  });

  // /tip/<tip_GUS>/ T1
  // XXX this is not implemented for the moment.
  // We need to invert the order of the parameters to make it uniform with the rest of the API.
  //$httpBackend.whenPOST('/submission/files/<submission_id>');

  $httpBackend.whenGET(/\/tip\/(.*)/).
    respond(function(method, url, data){
    var tip_resource = {
      "access_counter": 2,
      "access_limit": 42,
      "context_gus": "c_IZLJpOxNSXeuMQnuLZCm",
      "context_name": "An Example Context",
      "creation_date": "Wed Feb  6 10:35:42 2013",
      "download_limit": 42,
      "escalation_threshold": "None",
      "expiration_date": "Wed Feb  6 10:35:42 2013",
      "fields": {
          "somename": "some value"
      },
      "folders": [
        {
        "name": "Widgets",
        "upload_date": "Wed Feb  6 10:35:42 2013",
        "files": [{
          "filename": "foo.avi",
          "hash": "xxxxxxxxxxxxxxxx",
          "upload_date": "Wed Feb  6 10:35:42 2013",
          "download": "/file/xxxxxxxxxxxxxxxxx"
          },
          {
            "filename": "foo2.avi",
            "hash": "xxxxxxxxxxxxxxxx",
            "download": "/file/xxxxxxxxxxxxxxxxx",
            "upload_date": "Wed Feb  6 10:35:42 2013"
          }]
        },
        {
        "name": "Widgets 2",
        "upload_date": "Wed Feb  7 10:35:42 2013",
        "files": [{
          "filename": "foobar.avi",
          "hash": "xxxxxxxxxxxxxxxx",
          "upload_date": "Wed Feb  7 10:35:42 2013",
          "download": "/file/xxxxxxxxxxxxxxxxx"
          },
          {
            "filename": "foobar2.avi",
            "hash": "xxxxxxxxxxxxxxxx",
            "download": "/file/xxxxxxxxxxxxxxxxx",
            "upload_date": "Wed Feb  7 10:35:42 2013"
          }]
        }
      ],
      "id": "3043786039",
      "internaltip_id": 1,
      "last_access": "Never",
      "last_activity": "Wed Feb  6 10:35:42 2013",
      "mark": "new",
      "pertinence": "0",
      "receipt": "3043786039",
      "receivers": [
          "r_bJgDoEilpvJxydvrzOoa",
          "r_scIBPjjSnUUcINIaflTl"
      ]
    };

    return [200, tip_resource];
  });


  // * /tips/<tip_GUS> T2
  $httpBackend.whenPOST(/\/tips\/(.*)/).
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
      'description': "The description of the node",
      'name': "The name of the node",
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
    console.log("GET /admin/contexts");
    return [200, contexts];
  });

  $httpBackend.whenPOST('/admin/contexts').
    respond(function(method, url, data){
    console.log("POST /admin/contexts");
    console.log(data);
    return [200, data];
  });

  // * /admin/context A3
  $httpBackend.whenGET('/admin/context').
    respond(function(method, url, data){
      var context_resource = [{
          "context_gus": "c_IZLJpOxNSXeuMQnuLZCm",
          "description": "This is the an example context description",
          "escalation_threshold": null,
          "fields": [
              {
                  "hint": "This is the hint for the label",
                  "label": "Some Label",
                  "name": "somename",
                  "type": "text"
              }
          ],
          "file_max_download": 42,
          "languages": [],
          "name": "An Example Context",
          "receivers": [
              "r_bJgDoEilpvJxydvrzOoa",
              "r_scIBPjjSnUUcINIaflTl"
          ],
          "selectable_receiver": true,
          "tip_max_access": 42,
          "tip_timetolive": 42,
          "submission_timetolive": 42
      }];

      return [200, context_resource];
  });

  $httpBackend.whenPOST('/\/admin\/context(.*)/').
    respond(function(method, url, data){
      console.log(method);
      console.log(url);
      console.log(data);

      var response = {};
      return [200, response];
  });

  $httpBackend.whenPUT('/\/admin\/context(.*)/').
    respond(function(method, url, data){
      console.log(method);
      console.log(url);
      console.log(data);

      var response = {};
      return [200, response];
  });


  // * /admin/receivers A4
  $httpBackend.whenGET('/admin/receiver').
    respond(function(method, url, data){
      var receiver_resource = [{
        "can_configure_delivery": true,
        "can_configure_notification": true,
        "can_delete_submission": true,
        "can_postpone_expiration": true,
        "contexts": [
          "c_IZLJpOxNSXeuMQnuLZCm"
        ],
        "creation_date": "Wed Feb  6 09:18:59 2013",
        "description": "An Example Receiver",
        "languages": [
          "en",
          "it"
        ],
        "name": "An Example Receiver",
        "receiver_gus": "r_bJgDoEilpvJxydvrzOoa",
        "receiver_level": 1,
        "tags": [],
        "update_date": "Wed Feb  6 09:19:21 2013"
      },
      {
        "can_configure_delivery": true,
        "can_configure_notification": true,
        "can_delete_submission": true,
        "can_postpone_expiration": true,
        "contexts": [
          "c_IZLJpOxNSXeuMQnuLZCm"
        ],
        "creation_date": "Wed Feb  6 09:19:25 2013",
        "description": "An Example Receiver 2",
        "languages": [
          "en",
          "it"
        ],
        "name": "An Example Receiver 2",
        "receiver_gus": "r_scIBPjjSnUUcINIaflTl",
        "receiver_level": 1,
        "tags": [],
        "update_date": "Wed Feb  6 09:35:23 2013"
      }];
      return [200, receiver_resource];
  });

  $httpBackend.whenPOST('/admin/receiver').
    respond(function(method, url, data){
      console.log("POST /admin/receiver");
      console.log(method);
      console.log(url);
      console.log(data);
      return [200, data];
  });

  // * /admin/notification
  $httpBackend.whenGET('/admin/notification').
    respond(function(method, url, data){
      console.log("GET /admin/notification");
      var response = {
        'email': {
          'smtp_address': '',
          'smtp_port': 443,
          'smtp_username': '',
          'smtp_password': ''
        }
      };
      return [200, response];
  });

  // * /admin/notification
  $httpBackend.whenPOST('/admin/notification').
    respond(function(method, url, data){
      console.log("POST /admin/notification");
      console.log(data);
      return [200, data];
  });

  // * /admin/plugins A6
  $httpBackend.whenGET('/admin/plugins').
    respond(function(method, url, data){
      console.log("GET /admin/plugins");
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
