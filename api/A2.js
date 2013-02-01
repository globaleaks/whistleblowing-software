// This uses:
// https://github.com/visionmedia/supertest
// and mocha

/*
 
Thi test evaluates the following requirements for A2

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

var dummyContext = {
    name: 'dummyContext',
    description: 'dummyContextDescription',
    selectable_receiver: false,
    languages_supported: ['en', 'it'],
    fields: [],
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


  it("POST if name' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['name'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if description' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['description'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if selectable_receiver' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['selectable_receiver'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if languages_supported' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['languages_supported'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if tip_max_access' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['tip_max_access'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if time_tolive' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['tip_timetolive'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if file_max_download' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['file_max_download'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if escalation_threshold' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['escalation_threshold'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if receivers' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['receivers'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if fields' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['fields'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if invalid 'name' attribute inside the provided context FAIL (406", function(done){

    var test = clone(dummyContext);
    test['name'] = invalidField();

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if invalid 'description' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['description'] = invalidField();

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if invalid 'selectable_receiver' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['selectable_receiver'] = invalidField();

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if invalid 'languages_supported' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['languages_supported'] = invalidField();

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if invalid 'tip_max_access' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['tip_max_access'] = invalidField();

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if invalid 'time_tolive' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['tip_timetolive'] = invalidField();

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if invalid 'file_max_download' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['file_max_download'] = invalidField();

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if invalid 'escalation_threshold' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['escalation_threshold'] = invalidField();

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if invalid 'receivers' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['receivers'] = invalidField();

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if invalid 'fields' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['fields'] = invalidField();

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if unexpected attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['antani'] = "antani";

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("POST if both 'selectable_receiver' and 'escalation_threshold' are present FAIL (409)", function(done){

    var test = clone(dummyContext);
    test['selectable_receiver'] = true;
    test['escalation_threshold'] = 42;

    request()
    .post('/admin/context')
    .send(test)
    .expect(409, done);

  });


  it("PUT if correct context is provided SUCCESS (200)", function(done){

    var test = clone(dummyContext);
    test['name'] = 'antani';
    test['escalation_threshold'] = 42;

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .end(function(err, res){
        if (err) return done(err);
        var response = JSON.parse(res.text);

        response.should.have.property('name');
        response['name'].should.equal(test['name']);

        done();
      });

    });

  });

  it("PUT if name' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['name'];

    request()
    .post('/admin/context')
    .send(test)
    .expect(406, done);

  });

  it("PUT if description' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['description'];

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if selectable_receiver' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['selectable_receiver'];

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if languages_supported' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['languages_supported'];

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if tip_max_access' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['tip_max_access'];

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if time_tolive' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['tip_timetolive'];

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if file_max_download' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['file_max_download'];

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if escalation_threshold' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['escalation_threshold'];

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if receivers' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['receivers'];

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if fields' attribute lacks inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    delete test['fields'];

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if invalid 'name' attribute inside the provided context FAIL (406", function(done){

    var test = clone(dummyContext);
    test['name'] = invalidField();

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if invalid 'description' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['description'] = invalidField();

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if invalid 'selectable_receiver' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['selectable_receiver'] = invalidField();

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if invalid 'languages_supported' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['languages_supported'] = invalidField();

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if invalid 'tip_max_access' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['tip_max_access'] = invalidField();

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if invalid 'time_tolive' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['tip_timetolive'] = invalidField();

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if invalid 'file_max_download' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['file_max_download'] = invalidField();

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if invalid 'escalation_threshold' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['escalation_threshold'] = invalidField();

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if invalid 'receivers' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['receivers'] = invalidField();

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

  it("PUT if invalid 'fields' attribute inside the provided context FAIL (406)", function(done){

    var test = clone(dummyContext);
    test['fields'] = invalidField();

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(406, done);

    });

  });

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

  it("PUT if both 'selectable_receiver' and 'escalation_threshold' are present FAIL (409)", function(done){

    var test = clone(dummyContext);
    
    test['selectable_receiver'] = true;
    test['escalation_threshold'] = 42;

    getSomeContextID(function(contextID){

      request()
      .put('/admin/context/'+contextID)
      .send(test)
      .expect(409, done);

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
