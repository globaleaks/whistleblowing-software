// This uses:
// https://github.com/visionmedia/supertest
// and mocha

var request = require('supertest'),
  should = require('should');

// Tells where the backend is listening
//request = request.bind(request, 'http://192.168.33.102:8082');
request = request.bind(request, 'http://127.0.0.1:8082');

describe("Node Admin API functionality", function(){

  var dummyFields = [{'label': 'Some Fancy Name',
      'name': 'someFancyName',

      'value': 'I will appear by default',
      'hint': 'I will help you understand what I mean',

      'required': false,
      'type': 'text'
  }];

  var dummyContext = {
      name: 'dummyContext',
      description: 'dummyContextDescription',
      //languages_supported: ['en', 'it'],
      fields: [],

      escalation_threshold: 42,
      file_max_download: 42,
      tip_max_access: 42,
      selectable_receiver: true,
      tip_timetolive: 42,
      receivers: []
  };

  var dummyContextWithFields = {
      name: 'dummyContext',
      description: 'dummyContextDescription',
      //languages_supported: ['en', 'it'],
      fields: dummyFields,

      escalation_threshold: 42,
      file_max_download: 42,
      tip_max_access: 42,
      selectable_receiver: true,
      tip_timetolive: 42,
      receivers: []
  };

  var invalidContextNoName = {
      description: 'dummyContextDescription',
      //languages_supported: ['en', 'it'],
      fields: dummyFields,

      escalation_threshold: 42,
      file_max_download: 42,
      tip_max_access: 42,
      selectable_receiver: true,
      tip_timetolive: 42
  };

// {
//   "name":"Testing", 
//   "description":"Testing", 
//   "notification_selected":"email",
//   "notification_fields":"admin@example.com", 
//   "know_languages":["en","it"],
//   "can_postpone_expiration":true, 
//   "can_configure_delivery":true,
//   "can_delete_submission":true, 
//   "delivery_selected":"local",
//   "delivery_fields":"",
//   "receiver_level":1, 
//   "tags": ["tag1","tag2","tag3"], 
//   "contexts":[]
// }

  var dummyReceiver = {
    name: 'dummyName',
    description: 'dummyDescription',
    //can_postpone_expiration: true,
    //tags: ['tag1', 'tag2', 'tag3'],

    contexts: [],

    //can_configure_notification: true,
    //can_configure_delivery: true,
    can_delete_submission: true,
    password: '',
    old_password: '',

    receiver_level: 1,
    //languages: ['en', 'it'],
    //notification_selected: 'email',
    notification_fields: {'mail_address': 'admin@example.com'},

    //delivery_selected: 'local',
    //delivery_fields: ''

  };

  var dummyContextID = 'c_ElevenCharsNineChars';
  var dummyReceiverID = 'r_ElevenCharsNineChars';
  var dummyTipID = 'someRandomString';

  var dummySubmission = {
    //real_receipt: 'foobar',
    creation_time: 'globaleaks.rest.base.timeType',
    receivers: [dummyReceiverID],
    // XXX perhaps this should go as a paramater
    submission_gus: 'XXX',
    wb_fields: [
      {'someFancyName': 'Some Fancy Content'}
    ],
    expiration_time: 'XXX',
    context_gus: 'XXX',
    // files: ['']
  };

  var getSomeContextID = function(fn) {
    request()
    .get('/admin/context')
    .end(function(err, res){
      var response = JSON.parse(res.text);
      /* console.log(response); */
      fn(response[0].context_gus)
    });
  }

  // before(function(done){
  //   // Delete all the configured contexts
  //   request()
  //   .get('/admin/context')
  //   .expect(200)
  //   .end(function(err, res){
  //     if (err) return done(err);
  //     if (!res.text.length == 0){
  //       done();
  //     }
  //     var response = JSON.parse(res.text);

  //     for (var i in response) {
  //       console.log('deleting ' + response[i].context_gus)
  //       request()
  //       .del('/admin/context/' + response[i].context_gus)
  //       .expect(200)
  //       .end(function(err, res){
  //         request()
  //         .post('/admin/context')
  //         .send(dummyContext)
  //         .expect(201)
  //         .end(function(err, res){
  //           if (err) return done(err);
  //           var response = JSON.parse(res.text);
  //           dummyContextID = response['context_gus'];
  //           done();
  //         });
  //       });
  //     }
  //   });
  // });


  it("Should allow the Node Admin to access the admin interface", function(done){

    request()
    .get('/admin/node')
    .expect(200)
    .end(function(err, res){
      var response = JSON.parse(res.text);

      // console.log("----------------");
      // console.log(res.text);
      // console.log("----------------");

      response.should.have.property('name');
      response.should.have.property('description');

      response.should.have.property('hidden_service');

      response.should.have.property('public_site');
      response.should.have.property('stats_update_time');
      //response.should.have.property('public_stats_update_time');
      //response.should.have.property('private_stats_update_time');

      response.should.have.property('languages');

      done();

    });

  });

//   it("Should allow the Node Admin to change it's password", function(done){
// 
//     request()
//     .put('/admin/settings')
//     .send({'password': 'foobar'})
//     .expect(200, done);
// 
//   });

  it("Should allow the Node Admin to add context", function(done){

    request()
    .post('/admin/context')
    .send(dummyContext)
    .expect(201, done);

  });

  it("Should create an error when the Node Admin does not specify a name", function(done){
    // console.log(response);
    // console.log(contextID);
    // response.should.be.a('object');

    request()
    .put('/admin/context/' + dummyContextID)
    .send(invalidContextNoName)
    .expect(404)
    .end(function(err, res){
      var response = JSON.parse(res.text);
      should.exist(response['error_message']);
      done();
    });

  });

  it("Should allow the Node Admin to add and edit context", function(done){

    request()
    .post('/admin/context')
    .send(dummyContext)
    .expect(201)
    .end(function(err, res){
      if (err) return done(err);
      var response = JSON.parse(res.text),
        contextID = response['context_gus'],
        updatedContext = dummyContext;

      updatedContext['name'] = 'dummyContextChanged';

      // console.log(response);
      // console.log(contextID);
      // response.should.be.a('object');

      request()
      .put('/admin/context/' + contextID)
      .send(dummyContext)
      .expect(200)
      .expect(/dummyContextChanged/, done);

    });

  });


  it("Should allow the Node Admin to list contexts", function(done){

    request()
    .get('/admin/context')
    .expect(200)
    .end(function(err, res){
      if (err) return done(err);

      // console.log("----------------");
      // console.log(res.text);
      // console.log("----------------")

      var response = JSON.parse(res.text);
      response.indexOf(0);
      done();
    });

  });

  it("Should allow the Node Admin to list receivers", function(done){

    request()
    //put('/admin/receiver').
    .get('/admin/receiver')
    .expect(200)
    .end(function(err, res){
      if (err) return done(err);

      // console.log("----------------");
      // console.log(res.text);
      // console.log("----------------");

      done();
    });

  });

  it("Should allow the Node Admin to add receiver details", function(done){
    request()
    .post('/admin/receiver')
    .send(dummyReceiver)
    .expect(201)
    .end(function(err, res){
      if (err) {
        // console.log("allow the Node Admin to add receiver details");
        // console.log(res.text);
        return done(err);
      }
      var response = JSON.parse(res.text);

      response.should.have.property('receiver_gus');

      // console.log("-----2----------");
      // console.log(err);
      // console.log(res.text);
      // console.log("----------------")

      done();
    });

  });

  it("Should allow the Node Admin to add a context and receiver details", function(done){
    request()
    .post('/admin/context')
    .send(dummyContext)
    .expect(201)
    .end(function(err, res){
      if (err) return done(err);
      var response = JSON.parse(res.text),
        contextID = response['context_gus'];

      response.should.have.property('name');
      response.should.have.property('description');

      // console.log("-------1--------");
      // console.log(err);
      // console.log(res.text);
      // console.log("----------------")

     dummyReceiver.contexts.push(contextID);

      request()
      //put('/admin/receiver').
      .post('/admin/receiver')
      .send(dummyReceiver)
      .expect(201)
      .end(function(err, res){
        if (err) {
          console.log(res.text);
          return done(err);
        }

        var response = JSON.parse(res.text);

        response.should.have.property('receiver_gus');
        response['contexts'][0].should.equal(contextID);

        // console.log("-----2----------");
        // console.log(err);
        // console.log(res.text);
        // console.log("----------------")

        done();
      });
    });

  });

  it("Should add the receiver to the default context when only one context exists", function(done){
    request()
    .get('/admin/context')
    .expect(200)
    .end(function(err, res){
      if (err) return done(err);
      var response = JSON.parse(res.text),
        defaultContextID = response[0].context_gus;

      request()
      .post('/admin/receiver')
      .send(dummyReceiver)
      .expect(201)
      .end(function(err, res){
        if (err) {
          console.log(res.text);
          return done(err);
        }

        var response = JSON.parse(res.text);

        response.should.have.property('receiver_gus');
        should.exist(response['contexts'][0]);

        // console.log("-----2----------");
        // console.log(err);
        // console.log(res.text);
        // console.log("----------------")

        done();
      });
    });
  });

  it("Should allow the Node Admin to add a context and receiver details", function(done){
    request()
    .post('/admin/context')
    .send(dummyContext)
    .expect(201)
    .end(function(err, res){
      if (err) return done(err);
      var response = JSON.parse(res.text),
        contextID = response['context_gus'];

      response.should.have.property('name');
      response.should.have.property('description');

      // console.log("-------1--------");
      // console.log(err);
      // console.log(res.text);
      // console.log("----------------")

     dummyReceiver.contexts.push(contextID);

      request()
      //put('/admin/receiver').
      .post('/admin/receiver')
      .send(dummyReceiver)
      .expect(201)
      .end(function(err, res){
        if (err) {
          console.log(res.text);
          return done(err);
        }

        var response = JSON.parse(res.text);

        response.should.have.property('receiver_gus');
        should.exist(response['contexts'][0]);

        // console.log("-----2----------");
        // console.log(err);
        // console.log(res.text);
        // console.log("----------------")

        done();
      });
    });

  });

//   it("Should allow the Node Admin to add email details for configuration", function(done){
//
//     request()
//     // XXX not sure
//     .post('/admin/plugins/')
//     .end(function(err, res){
//       if (err) return done(err);
//       done();
//     });
//
//   });
//

  it("Should allow the Node Admin to configure submission form", function(done){

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(dummyContextWithFields)
      .end(function(err, res){
        if (err) return done(err);
        var response = JSON.parse(res.text);
        /* console.log(response); */

        response['fields'][0]['name']
        .should.equal(dummyContextWithFields['fields'][0]['name']);

        done();
      });

    });

  });

});


// describe("Whistleblower API functionality", function(){
//   it("Should allow the Whistleblower to access whistleblowing website", function(done){
// 
//     request()
//     .put('/node')
//     .expect(200, done);
// 
//   });
// 
//   it("Should allow the Whistleblower to select a context", function(done){
// 
//     request()
//     .post('/submission')
//     .send({'c_id': dummyContextID})
//     .expect(201)
//     .end(function(err, res){
//       if (err) return done(err);
// 
//       var response = JSON.parse(res.text),
//         submissionID = response['id'];
// 
//       request()
//       .post('/submission/'+submissionID)
//       .send({'context_gus': dummyContextID})
//       .expect(200, done);
// 
//     });
// 
//   });
// 
//   it("Should allow the Whistleblower to submit form data", function(done){
// 
//     request()
//     .post('/submission')
//     .send({'c_id': dummyContextID})
//     .expect(201)
//     .end(function(err, res){
//       if (err) return done(err);
// 
//       var response = JSON.parse(res.text),
//         submissionID = response['id'];
// 
//       request()
//       .post('/submission/'+submissionID)
//       .send(dummySubmission)
//       .expect(200, done);
// 
//     });
// 
//   });
// 
//   it("Should allow the Whistleblower to add one or more files on submission interface", function(){
// 
//   });
// 
//   it("Should allow the Whistleblower to receive a Receipt", function(done){
// 
//     request()
//     .post('/submission')
//     .send({'c_id': dummyContextID})
//     .expect(201)
//     .end(function(err, res){
//       if (err) return done(err);
// 
//       var response = JSON.parse(res.text),
//         submissionID = response['id'];
// 
//       request()
//       .post('/submission/' + submissionID)
//       .send(dummySubmission)
//       .expect(200)
//       .end(function(err, res){
//         if (err) return done(err);
// 
//         var response = JSON.parse(res.text),
//           receiptID = response['real_receipt'];
// 
//         done();
//       });
// 
//     });
// 
//   });
// 
//   it("Should allow the Whistleblower to access his Tip with it's Receipt", function(done){
// 
//     request()
//     .get('/tip/' + dummyTipID)
//     .expect(200, done);
// 
//   });
// 
//   it("Should allow the Whistleblower to add comments to his Tip", function(done){
// 
//     request()
//     .post('/tip/' + dummyTipID + '/comments')
//     .expect(201, done);
// 
//   });
// 
//   it("Should allow the Whistleblower to see all comments to his Tip", function(done){
// 
//     request()
//     .get('/tip/' + dummyTipID + '/comments')
//     .expect(200, done);
// 
//   });
// 
//   it("Should allow the Whistleblower to add new files to his Tip", function(done){
// 
//     // Separate API
//     done();
// 
//   });
// 
//   it("Should allow the Whistleblower to see access/download statistics", function(done){
// 
//     request()
//     .get('/tip/' + dummyTipID)
//     .expect(/tip/)
//     .expect(/comments/)
//     .end(function(err, res){
//       if (err) return done(err);
//       done();
//     });
// 
//   });
// 
// });
// 
// describe("Receiver API functionality", function(){
// 
//   it("Should allow the Receiver to get notified of a new Tip by email", function(done){
//     done();
//   });
// 
//   it("Should allow the Receiver to get notified of a new files or comment on existing Tip by email", function(done){
// 
//     request()
//     .end(function(err, res){
//       if (err) return done(err);
//       done();
//     });
// 
//   });
// 
//   it("Should allow the Receiver to access his Tip by clicking on Tip link receiver by email", function(done){
// 
//     request()
//     .end(function(err, res){
//       if (err) return done(err);
//       done();
//     });
// 
//   });
// 
//   it("Should allow the Receiver to download files received on his Tip", function(done){
// 
//     request()
//     .end(function(err, res){
//       if (err) return done(err);
//       done();
//     });
// 
//   });
// 
//   it("Should allow the Receiver to add a comment on his Tip", function(done){
//     request()
//     .end(function(err, res){
//       if (err) return done(err);
//       done();
//     });
// 
//   });
// 
//   it("Should allow the Receiver to see all comments on his Tip", function(done){
//     request()
//     .end(function(err, res){
//       if (err) return done(err);
//       done();
//     });
//   });
// 
//   it("Should allow the Receiver to see access/download statistics", function(done){
//     request()
//     .end(function(err, res){
//       if (err) return done(err);
//       done();
//     });
//   });
// 
// });
// 
