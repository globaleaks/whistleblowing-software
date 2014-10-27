// This uses:
// https://github.com/visionmedia/supertest
// and mocha

/*
 
This test evaluates the following requirements for A2 (/admin/context)

    GET/PUT/DELETE should fail if non existent 'context_gus' is provided (404)
    GET/PUT/DELETE should succeed if existent 'context_gus' is provided (200)
    POST/PUT should succeed if 'valid context is provided (200)
    POST/PUT if 'name attribute is missing inside the provided context (406)
    POST/PUT if 'description' attribute is missing inside the provided context (406)
    POST/PUT if 'selectable_receiver' attribute is missing inside the provided context (406)
    POST/PUT if 'languages_supported' attribute is missing inside the provided context (406)
    POST/PUT if 'tip_max_access' attribute is missing inside the provided context (406)
    POST/PUT if 'time_tolive' attribute is missing inside the provided context (406)
    POST/PUT if 'file_max_download' attribute is missing inside the provided context (406)
    POST/PUT if 'escalation_threshold' attribute is missing inside the provided context (406)
    POST/PUT if 'receivers' attribute is missing inside the provided context (406)
    POST/PUT if 'fields' attribute is missing inside the provided context (406)
    POST/PUT if invalid 'name' attribute inside the provided context (406)
    POST/PUT if invalid 'description' attribute inside the provided context (406)
    POST/PUT if invalid 'selectable_receiver' attribute inside the provided context (406)
    POST/PUT if invalid 'languages_supported' attribute inside the provided context (406)
    POST/PUT if invalid 'tip_max_access' attribute inside the provided context (406)
    POST/PUT if invalid 'time_tolive' attribute inside the provided context (406)
    POST/PUT if invalid 'file_max_download' attribute inside the provided context (406)
    POST/PUT if invalid 'escalation_threshold' attribute inside the provided context (406)
    POST/PUT if invalid 'receivers' attribute inside the provided context (406)
    POST/PUT if invalid 'fields' attribute inside the provided context (406)
    POST/PUT if unexpected attribute inside the provided context (406)
    POST/PUT if both 'selectable_receiver' and 'escalation_threshold' are present (406)

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

var getSomeContextID = function(fn) {
  request()
  .get('/admin/context')
  .end(function(err, res){
    var response = JSON.parse(res.text);
    fn(response[0].context_gus)
  });
}

/*
  specification = {
      'context_gus': contextGUS,
      'name': unicode,
      'description': unicode,
      'selectable_receiver': bool,
      'languages': list,
      'tip_max_access' : int,
      'tip_timetolive' : int,
      'file_max_download' : int,
      'escalation_threshold' : int,
      'receivers' : [ receiverGUS ],
      'fields': [ formFieldsDict ]
  });

  notes: 'selectable_receiver' and 'escalation_threshold' are mutually exclusives.

*/

var args = [
           "name",
           "description",
           "selectable_receiver",
           "languages_supported",
           "fields",
           "tip_max_access",
           "tip_timetolive",
           "file_max_download",
           "escalation_threshold",
           "receivers",
           "fields"
           ];

var dummyContext = {
    name: 'dummyContext',
    description: 'dummyContextDescription',
    selectable_receiver: false,
    languages_supported: ['en', 'it'],
    tip_max_access: 42,
    tip_timetolive: 42,
    file_max_download: 42,
    escalation_threshold : 42,
    receivers: [],
    fields: []
}

var dummyContextUpdate = {
    name: 'update',
    description: 'update',
    selectable_receiver: false,
    languages_supported: ['de', 'pl'],
    tip_max_access: 24,
    tip_timetolive: 24,
    file_max_download: 24,
    escalation_threshold : 24,
    receivers: [],
    fields: []
}

describe("Node Admin API Context functionality", function(){

  it("should succeed if valid context is provided (POST, 200)", function(done){

    var test = clone(dummyContext);

    request()
    .post('/admin/context')
    .send(test)
    .expect(201, done);

  });

  args.forEach(function (arg) {

    it("should fail if the '" + arg + "' attribute is missing inside the provided context (POST, 406)", function(done){

      var test = clone(dummyContext);
      delete test[arg];

      request()
      .post('/admin/context')
      .send(test)
      .expect(406, done)

    });

  })

  args.forEach(function (arg) {

    it("should fail if an invalid '" + arg + "' attribute is present inside the provided context (POST, 406)", function(done){

      var test = clone(dummyContext);
      test[arg] = invalidField();

      request()
      .post('/admin/context')
      .send(test)
      .expect(406, done)

    });

  })


  it("should fail if an additional attribute inside the provided context (PUT, 406)", function(done){

    var test = clone(dummyContext);
    test['antani'] = "antani";

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done)

    });

  });

  it("should fail if both 'selectable_receiver' and 'escalation_threshold' are present (PUT, 406)", function(done){

    var test = clone(dummyContext);
    
    test['selectable_receiver'] = true;
    test['escalation_threshold'] = 42;

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done)

    });
  
  });

  it("should succeed if an existent context_gus is provided (GET, 200)", function(done){

    getSomeContextID(function(contextID){

      request()
      .get('/admin/context/'+contextID)
      .send()
      .expect(200)
      .end(function(err, res){
        if (err) return done(err);
        var response = JSON.parse(res.text);
        response.should.have.property('name');
        done();
      });

    });
  
  });

  args.forEach(function (arg) {

    it("should succeed if an invalid update for the attribute '" + arg + "' is provided (PUT, 200)", function(done){

      var test = clone(dummyContext);
      test[arg] = invalidField();

      getSomeContextID(function(contextID){

        request()
        .put('/admin/context/'+contextID)
        .send(test)
        .expect(406, done)

      });
  
    });

  });

  args.forEach(function (arg) {

    it("should succeed if a valid update for the attribute '" + arg + "' is provided (PUT, 200)", function(done){

      var test = clone(dummyContext);
      test[arg] = dummyContextUpdate[arg];

      getSomeContextID(function(contextID){

        request()
        .put('/admin/context/'+contextID)
        .send(test)
        .expect(200, done)
      });
  
    });

    it("should fail if previous valid update for the attribute '" + arg + "' is not committed (GET, 200)", function(done){

      getSomeContextID(function(contextID){

        request()
        .get('/admin/context/'+contextID)
        .send()
        .end(function(err, res){
          if (err) return done(err);
          var response = JSON.parse(res.text);
          response.should.have.property('name');
          response.should.have.property(arg);
          response[arg].should.eql(dummyContextUpdate[arg]);
          done()
        });

      });
  
    });

  });

  it("should fail if a not existent context_gus is provided (GET, 404)", function(done){

    request()
    .get('/admin/context/c_01010101010101010101')
    .send()
    .expect(404, done)
  });
  
  it("should succeed if an existent context_gus is provided (DELETE, 200)", function(done){

    getSomeContextID(function(contextID){

    request()
    .del('/admin/context/'+contextID)
    .set('Content-Length', 0)
    .expect(200)
    .end(function(err, res) {
      if (err) return done(err);
      request()
      .get('/admin/context/'+contextID)
      .send()
      .expect(404, done)
    })

    });
  });
  
  it("should fail if a not existent context_gus is provided (DELETE, 404)", function(done){

    request()
    .del('/admin/context/c_01010101010101010101')
    .set('Content-Length', 0)
    .expect(404, done)

  
  });

});
