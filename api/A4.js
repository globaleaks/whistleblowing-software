// This uses:
// https://github.com/visionmedia/supertest
// and mocha

/*
 
Thi test evaluates the following requirements for A4 (/admin/receiver)

    GET/PUT/DELETE should fail if non existent 'receiver_gus' is provided (404)
    GET/PUT/DELETE should succeed if existent 'receiver_gus' is provided (200)
    POST/PUT should succeed if 'correct receiver is provided (200)
    POST/PUT should fail if 'name attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'description' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'tags' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'languages' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'context' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'receiver_level' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'delivery_selected' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'delivery_fields' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'can_delete_submission' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'can_postpone_expiration' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'can_configure_delivery' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if 'can_configure_notification' attribute is missing inside the provided receiver (406)
    POST/PUT should fail if invalid 'name attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'description' attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'tags' attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'languages' attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'context' attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'receiver_level' attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'delivery_selected' attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'delivery_fields' attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'can_delete_submission' attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'can_postpone_expiration' attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'can_configure_delivery' attribute is present inside the provided receiver (406)
    POST/PUT should fail if invalid 'can_configure_notification' attribute is present inside the provided receiver (406)
    POST/PUT should fail if unexpected attribute is present inside the provided receiver (406)

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

  it("should succeed if a correct receiver is provided (POST, 200)", function(done){

    var test = clone(dummyReceiver);

    request()
    .post('/admin/receiver')
    .send(test)
    .expect(201, done);

  })

  it("should fail if an attribute is missing inside the provided receiver (POST, 406)", function(done){
      args.forEach(function (arg) {

        var test = clone(dummyReceiver);
        delete test[arg];

        request()
        .post('/admin/receiver')
        .send(test)
        .expect(406, done);

      });
  })

  it("should fail if an invalid attribute is present inside the provided receiver (POST, 406)", function(done){
      args.forEach(function (arg) {

        var test = clone(dummyReceiver);
        test[arg] = invalidField();

        request()
        .post('/admin/receiver')
        .send(test)
        .expect(406, done);

      });
  })

  it("should fail if an additional attribute is present inside the provided Receiver (PUT, 406)", function(done){

    var test = clone(dummyReceiver);
    test['antani'] = "antani";

    getSomeReceiverID(function(ReceiverID){

      request()
      .put('/admin/receiver/'+ReceiverID)
      .send(test)
      .expect(406, done);

    });

  });

  it("should succeed if an existent receiver_gus is provided (GET, 200)", function(done){

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

  it("should fail if not existent receiver_gus is provided (GET, 404)", function(done){

    request()
    .get('/admin/receiver/r_01010101010101010101')
    .send()
    .expect(404, done)

  });
  
  it("should succeed if an existent receiver_gus is provided (DELETE, 200)", function(done){

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
  
  it("should fail if a not existent receiver_gus is provided (DELETE, 404)", function(done){

    request()
    .del('/admin/receiver/r_01010101010101010101')
    .expect(404, done)
  
  });

});
