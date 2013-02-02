// This uses:
// https://github.com/visionmedia/supertest
// and mocha

/*
 
Thi test evaluates the following requirements for A4 (/admin/receiver)

    GET/PUT/DELETE if non existent 'receiver_gus' is provided FAIL (404)
    GET/PUT/DELETE if existent 'receiver_gus' is provided SUCCESS (200)
    POST/PUT if 'correct receiver is provided SUCCESS (200)
    POST/PUT if 'name attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'description' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'tags' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'languages' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'context' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'receiver_level' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'delivery_selected' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'delivery_fields' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'can_delete_submission' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'can_postpone_expiration' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'can_configure_delivery' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if 'can_configure_notification' attribute lacks inside the provided receiver FAIL (406)
    POST/PUT if invalid 'name attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'description' attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'tags' attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'languages' attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'context' attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'receiver_level' attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'delivery_selected' attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'delivery_fields' attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'can_delete_submission' attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'can_postpone_expiration' attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'can_configure_delivery' attribute inside the provided receiver FAIL (406)
    POST/PUT if invalid 'can_configure_notification' attribute inside the provided receiver FAIL (406)
    POST/PUT if unexpected attribute inside the provided receiver FAIL (406)

*/

var request = require('supertest'), should = require('should');

// Tells where the backend is listening
request = request.bind(request, 'http://127.0.0.1:8082');

function clone(obj) {
    if (null == obj || "object" != typeof obj) return obj;
    var copy = obj.constructor();
    for (var attr in obj) {
        if (obj.hasOwnProperty(attr)) copy[attr] = obj[attr];
    }
    return copy;
}

function invalidField() {

}

var getSomeReceiverID = function(fn) {
  request()
  .get('/admin/receiver')
  .end(function(err, res){
    var response = JSON.parse(res.text);
    /* console.log(response); */
    fn(response[0].receiver_gus)
  });
}

/*

  specification =  {
      'receiver_gus' : receiverGUS,
      'name' : unicode,
      'description' : unicode,
      'tags': list,
      'languages' : list,
      'creation_date' : timeType,
      'update_date' : timeType,
      'last_access' : timeType,
      'contexts' : [ contextGUS ],
      'receiver_level' : int,
      'notification_selected' : unicode,
      'notification_fields' : unicode,
      'delivery_selected' : unicode,
      'delivery_fields' : unicode,
      'can_delete_submission' : bool,
      'can_postpone_expiration' : bool,
      'can_configure_delivery' : bool,
      'can_configure_notification' : bool
  }

  notes: 'selectable_receiver' and 'escalation_threshold' are mutually exclusives.

*/

var args = [
           "name",
           "description",
           "tags",
           "languages",
           "contexts",
           "receiver_level",
           "notification_selected",
           "notification_fields",
           "delivery_selected",
           "delivery_fields",
           "can_delete_submission",
           "can_postpone_expiration",
           "can_configure_delivery",
           "can_configure_notification"
           ];

var dummyReceiver = {
    name: 'dummyReceiver',
    description: 'dummyReceiverDescription',
    tags: ["123", "231", "312"],
    languages: [{"code": "it", "name": "Italiano"}, {"code": "en", "name": "English"}],
    contexts: [],
    receiver_level: 1,
    notification_selected: "email",
    notification_fields: "evilaliv3@globaleaks.org",
    delivery_selected: "local",
    delivery_fields: false,
    can_delete_submission: true,
    can_postpone_expiration: true,
    can_configure_delivery: true,
    can_configure_notification: true
};

describe("Node Admin API Receiver functionality", function(){

  it("POST if correct Receiver is provided SUCCESS (200)", function(done){

    var test = clone(dummyReceiver);

    request()
    .post('/admin/receiver')
    .send(test)
    .expect(201, done);

  })

  args.forEach(function (arg) {
      it("POST if '" + arg + "' attribute lacks inside the provided Receiver FAIL (406)", function(done){

        var test = clone(dummyReceiver);
        delete test[arg];

        request()
        .post('/admin/receiver')
        .send(test)
        .expect(406, done);

      });
  })

  args.forEach(function (arg) {
      it("POST if invalid '" + arg + "' attribute inside the provided Receiver FAIL (406)", function(done){

        var test = clone(dummyReceiver);
        test[arg] = invalidField();

        request()
        .post('/admin/receiver')
        .send(test)
        .expect(406, done);

      });
  })

  it("PUT if additional attribute inside the provided Receiver FAIL (406)", function(done){

    var test = clone(dummyReceiver);
    test['antani'] = "antani";

    getSomeReceiverID(function(ReceiverID){

      request()
      .put('/admin/receiver/'+ReceiverID)
      .send(test)
      .expect(406, done);

    });

  });

  it("GET if existent receiver_gus is provided SUCCESS (200)", function(done){

    var test = clone(dummyReceiver);

    getSomeReceiverID(function(ReceiverID){

      request()
      .get('/admin/receiver/'+ReceiverID)
      .send()
      .end(function(err, res){
        if (err) return done(err);
        var response = JSON.parse(res.text);

        response.should.have.property('name');

        done();
      });

    });
  
  });

  it("GET if not existent receiver_gus is provided FAIL (404)", function(done){

    request()
    .get('/admin/receiver/r_01010101010101010101')
    .send()
    .expect(404, done)

  });
  
  it("DELETE if existent receiver_gus is provided SUCCESS (200)", function(done){

    getSomeReceiverID(function(ReceiverID){

    request()
    .del('/admin/receiver/'+ReceiverID)
    .expect(200)
    .end(function(err, res) {
      request()
      .get('/admin/receiver/'+ReceiverID)
      .send()
      .end(function(err, res){
        if (err) return done(err);
        var response = JSON.parse(res.text);
        response.should.have.property('name');
        done();
      });
    })

    });
  });
  
  it("DELETE if not existent receiver_gus is provided FAIL (404)", function(done){

    request()
    .del('/admin/receiver/r_01010101010101010101')
    .expect(404, done)
  
  });

});
