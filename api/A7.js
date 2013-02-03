// This uses:
// https://github.com/visionmedia/supertest
// and mocha

/*
 
Thi test evaluates the following requirements for A2 (/admin/context)

    GET/PUT/DELETE should fail if non existent 'context_gus' is provided (404)
    GET/PUT/DELETE should succeed should fail if existent 'context_gus' is provided (200)
    POST/PUT should succeed should fail if 'correct context is provided (200)
    POST/PUT should fail if 'name attribute lacks inside the provided context (406)
    POST/PUT should fail if 'description' attribute lacks inside the provided context (406)
    POST/PUT should fail if 'selectable_receiver' attribute lacks inside the provided context (406)
    POST/PUT should fail if 'languages_supported' attribute lacks inside the provided context (406)
    POST/PUT should fail if 'tip_max_access' attribute lacks inside the provided context (406)
    POST/PUT should fail if 'time_tolive' attribute lacks inside the provided context (406)
    POST/PUT should fail if 'file_max_download' attribute lacks inside the provided context (406)
    POST/PUT should fail if 'escalation_threshold' attribute lacks inside the provided context (406)
    POST/PUT should fail if 'receivers' attribute lacks inside the provided context (406)
    POST/PUT should fail if 'fields' attribute lacks inside the provided context (406)
    POST/PUT should fail if invalid 'name' attribute inside the provided context (406)
    POST/PUT should fail if invalid 'description' attribute inside the provided context (406)
    POST/PUT should fail if invalid 'selectable_receiver' attribute inside the provided context (406)
    POST/PUT should fail if invalid 'languages_supported' attribute inside the provided context (406)
    POST/PUT should fail if invalid 'tip_max_access' attribute inside the provided context (406)
    POST/PUT should fail if invalid 'time_tolive' attribute inside the provided context (406)
    POST/PUT should fail if invalid 'file_max_download' attribute inside the provided context (406)
    POST/PUT should fail if invalid 'escalation_threshold' attribute inside the provided context (406)
    POST/PUT should fail if invalid 'receivers' attribute inside the provided context (406)
    POST/PUT should fail if invalid 'fields' attribute inside the provided context (406)
    POST/PUT should fail if unexpected attribute inside the provided context (406)
    POST/PUT should fail if both 'selectable_receiver' and 'escalation_threshold' are present (406)

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
    /* console.log(response); */
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
  }

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
};

describe("Node Admin API Context functionality", function(){

  it("POST should succeed if a correct context is provided (200)", function(done){

    var test = clone(dummyContext);

    request()
    .post('/admin/context')
    .send(test)
    .expect(201, done);

  });


  it("POST should fail if an attribute lacks inside the provided Context (406)", function(done){
      args.forEach(function (arg) {
        var test = clone(dummyContext);
        delete test[arg];

        request()
        .post('/admin/context')
        .send(test)
        .expect(406, done);

      });
  })

  it("POST should fail if an invalid attribute inside the provided Context (406)", function(done){
      args.forEach(function (arg) {

        var test = clone(dummyContext);
        test[arg] = invalidField();

        request()
        .post('/admin/context')
        .send(test)
        .expect(406, done);

      });
  })


  it("PUT should fail if an additional attribute inside the provided context (406)", function(done){

    var test = clone(dummyContext);
    test['antani'] = "antani";

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT should fail if both 'selectable_receiver' and 'escalation_threshold' are present (406)", function(done){

    var test = clone(dummyContext);
    
    test['selectable_receiver'] = true;
    test['escalation_threshold'] = 42;

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });
  
  });

  it("GET should fail if an existent context_gus is provided (200)", function(done){

    var test = clone(dummyContext);

    getSomeContextID(function(contextID){

      request()
      .get('/admin/context/'+contextID)
      .send()
      .end(function(err, res){
        if (err) return done(err);
        var response = JSON.parse(res.text);

        response.should.have.property('name');

        done();
      });

    });
  
  });

  it("GET should fail if a not existent context_gus is provided (404)", function(done){

    request()
    .get('/admin/context/c_01010101010101010101')
    .send()
    .expect(404, done)

  });
  
  it("DELETE should succeed if an existent context_gus is provided (200)", function(done){

    getSomeContextID(function(contextID){

    request()
    .del('/admin/context/'+contextID)
    .expect(200)
    .end(function(err, res) {
      request()
      .get('/admin/context/'+contextID)
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
  
  it("DELETE should fail if a not existent context_gus is provided (404)", function(done){

    request()
    .del('/admin/context/c_01010101010101010101')
    .expect(404, done)
  
  });

});
