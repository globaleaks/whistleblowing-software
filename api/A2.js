// This uses:
// https://github.com/visionmedia/supertest
// and mocha

/*
 
Thi test evaluates the following requirements for A2 (/admin/context)

    GET/PUT/DELETE if non existent 'context_gus' is provided FAIL (404)
    GET/PUT/DELETE if existent 'context_gus' is provided SUCCESS (200)
    POST/PUT if 'correct context is provided SUCCESS (200)
    POST/PUT if 'name attribute lacks inside the provided context FAIL (406)
    POST/PUT if 'description' attribute lacks inside the provided context FAIL (406)
    POST/PUT if 'selectable_receiver' attribute lacks inside the provided context FAIL (406)
    POST/PUT if 'languages_supported' attribute lacks inside the provided context FAIL (406)
    POST/PUT if 'tip_max_access' attribute lacks inside the provided context FAIL (406)
    POST/PUT if 'time_tolive' attribute lacks inside the provided context FAIL (406)
    POST/PUT if 'file_max_download' attribute lacks inside the provided context FAIL (406)
    POST/PUT if 'escalation_threshold' attribute lacks inside the provided context FAIL (406)
    POST/PUT if 'receivers' attribute lacks inside the provided context FAIL (406)
    POST/PUT if 'fields' attribute lacks inside the provided context FAIL (406)
    POST/PUT if invalid 'name' attribute inside the provided context FAIL (406)
    POST/PUT if invalid 'description' attribute inside the provided context FAIL (406)
    POST/PUT if invalid 'selectable_receiver' attribute inside the provided context FAIL (406)
    POST/PUT if invalid 'languages_supported' attribute inside the provided context FAIL (406)
    POST/PUT if invalid 'tip_max_access' attribute inside the provided context FAIL (406)
    POST/PUT if invalid 'time_tolive' attribute inside the provided context FAIL (406)
    POST/PUT if invalid 'file_max_download' attribute inside the provided context FAIL (406)
    POST/PUT if invalid 'escalation_threshold' attribute inside the provided context FAIL (406)
    POST/PUT if invalid 'receivers' attribute inside the provided context FAIL (406)
    POST/PUT if invalid 'fields' attribute inside the provided context FAIL (406)
    POST/PUT if unexpected attribute inside the provided context FAIL (406)
    POST/PUT if both 'selectable_receiver' and 'escalation_threshold' are present FAIL (409)

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

  it("POST if correct context is provided SUCCESS (200)", function(done){

    var test = clone(dummyContext);

    request()
    .post('/admin/context')
    .send(test)
    .expect(201, done);

  });


  args.forEach(function (arg) {
      it("POST if '" + arg + "' attribute lacks inside the provided Context FAIL (406)", function(done){

        var test = clone(dummyContext);
        delete test[arg];

        request()
        .post('/admin/context')
        .send(test)
        .expect(406, done);

      });
  })

  args.forEach(function (arg) {
      it("POST if invalid '" + arg + "' attribute inside the provided Context FAIL (406)", function(done){

        var test = clone(dummyContext);
        test[arg] = invalidField();

        request()
        .post('/admin/context')
        .send(test)
        .expect(406, done);

      });
  })


  it("PUT if additional attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['antani'] = "antani";

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if both 'selectable_receiver' and 'escalation_threshold' are present FAIL (406)", function(done){

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

  it("GET if existent context_gus is provided SUCCESS (200)", function(done){

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

  it("GET if not existent context_gus is provided FAIL (404)", function(done){

    request()
    .get('/admin/context/c_01010101010101010101')
    .send()
    .expect(404, done)

  });
  
  it("DELETE if existent context_gus is provided SUCCESS (200)", function(done){

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
  
  it("DELETE if not existent context_gus is provided FAIL (404)", function(done){

    request()
    .del('/admin/context/c_01010101010101010101')
    .expect(404, done)
  
  });

});
