/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest'),
  should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var population_order = 4;
var submission_population_order = 4;

var receivers = new Array();
var receivers_ids = new Array();
var contexts = new Array();
var contexts_ids = new Array();
var submissions = new Array();
var files = new Array();
var wb_keycodes  = new Array();

var validate_mandatory_headers = function(headers) {
  var mandatory_headers = {
    "X-XSS-Protection": "1; mode=block",
    "X-Robots-Tag": "noindex",
    "X-Content-Type-Options": "nosniff",
    "Expires": "-1",
    "Server": "globaleaks",
    "Pragma":  "no-cache",
    "Cache-control": "no-cache, no-store, must-revalidate"
  }

  for (var key in mandatory_headers) {
    if (headers[key.toLowerCase()] != mandatory_headers[key]) {
      throw key + " != " + mandatory_headers[key];
    }
  }
}

var valid_login = function(i) {
  return {
    "username": "",
    "password": wb_keycodes[i],
    "role": "wb"
  }
}

var invalid_login = function(i) {
  return {
    "username": "",
    "password": "antani",
    "role": "wb"
  }
}

var fill_field_recursively = function(field) {
  field['value'] = 'antani';
  for (var i = 0; i < field.children.length; j++) {
    fill_field_recursively(field.children[i]);
  };
}

var fill_steps = function(steps) {
  for (i in steps) {
    for (c in steps[i].children) {
      fill_field_recursively(steps[i].children[c]);
    }
  };

  return steps
}

describe('GET /contexts', function(){
  it('responds with ' + population_order + ' contexts associated to ' + population_order + ' receivers', function(done){
    app
      .get('/contexts')
      .expect('Content-Type', 'application/json')
      .expect(200)
      .end(function(err, res) {
        if (err) {
          return done(err);
        } else {

          validate_mandatory_headers(res.headers);

          if (res.body.length != population_order) {
            throw "/contexts didn't return " + population_order + " contexts";
          }

          contexts = res.body;

          for (var i=0; i<population_order; i++) {

            contexts_ids.push(contexts[i].id);

            if(contexts[i].receivers.length != population_order) {
              throw "/contexts didn't return " + population_order + " receivers associated to each context";
            }
          }

          done();
        }
      });
  })
})

describe('GET /receivers', function(){
  it('responds with ' + population_order + ' receivers associated to ' + population_order + ' contexts', function(done){
    app
      .get('/receivers')
      .expect('Content-Type', 'application/json')
      .expect(200)
      .end(function(err, res) {
        if (err) {
          return done(err);
        } else {

          validate_mandatory_headers(res.headers);

          if (res.body.length != population_order) {
            throw "/receivers didn't return " + population_order + " receivers";
          }

          receivers = res.body;

          for (var i=0; i<population_order; i++) {

            receivers_ids.push(receivers[i].id);

            if(receivers[i].contexts.length != population_order) {
              throw "/receivers didn't return " + population_order + " receivers associated to each receiver";
            }
          }

          done();
        }
      });
  })
})

describe('POST /submission', function(){
  for (var i=0; i<submission_population_order; i++) {
    (function (i) {
      it('responds with ', function(done){

        var new_submission = {};
        new_submission.context_id = contexts_ids[i];
        new_submission.receivers = receivers_ids;
        new_submission.wb_steps = fill_steps(contexts[i].steps);
        new_submission.files = [];
        new_submission.finalize = false;

        app
          .post('/submission')
          .send(new_submission)
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=antani')
          .expect('Content-Type', 'application/json')
          .expect(201)
          .end(function(err, res) {
            if (err) {
              return done(err);
            } else {

              validate_mandatory_headers(res.headers);

              submissions.push(res.body);

              done();
            }
          });

      })
    })(i);

  }
})

describe('POST /submission/submission_id/file', function(){
  for (var i=0; i<submission_population_order; i++) {
    (function (i) {
      it('responds with ', function(done){
        app
          .post('/submission/' + submissions[i].id + '/file')
          .send('ANTANIFILECONTENT')
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=antani')
          .set('Content-Type', 'text/plain')
          .set('Content-Disposition', 'attachment; filename="ANTANI.txt"')
          .expect('Content-Type', 'application/json')
          .expect(201)
          .end(function(err, res) {
            if (err) {
              return done(err);
            } else {

              validate_mandatory_headers(res.headers);

              submissions.push(res.body);

              done();
            }
          });

      })
    })(i);

  }
})

// finalize with missing receiver and empty fields must result in 412
describe('POST /submission', function(){
  for (var i=0; i<submission_population_order; i++) {
    (function (i) {
      it('responds with ', function(done){
        submissions[i].receivers = [];
        submissions[i].wb_steps = [];

        submissions[i].finalize = 'true';

        app
          .post('/submission')
          .send(submissions[i])
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=antani')
          .expect('Content-Type', 'application/json')
          .expect(412)
          .end(function(err, res) {
            if (err) {
              return done(err);
            } else {

              validate_mandatory_headers(res.headers);

              submissions.push(res.body);

              done();
            }
          });

      })
    })(i);
  }
})

describe('POST /submission', function(){
  for (var i=0; i<submission_population_order; i++) {
    (function (i) {

      it('responds with ', function(done){

        submissions[i].receivers = receivers_ids;
        submissions[i].wb_steps = fill_steps(contexts[i].steps);
        submissions[i].finalize = 'true';

        app
          .post('/submission')
          .send(submissions[i])
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=antani')
          .expect('Content-Type', 'application/json')
          .expect(201)
          .end(function(err, res) {
            if (err) {
              return done(err);
            } else {

              validate_mandatory_headers(res.headers);

              submissions.push(res.body);

              wb_keycodes.push(res.body.receipt);

              done();
            }
          });

      })
    })(i);
  }
})

// full test on first submission only
for (var i=0; i<1; i++){
  (function (i) {
    describe('POST /authentication', function () {
      it('responds 403 on valid wb login with missing XSRF token (missing header)', function (done) {
        var credentials = valid_login(i);
        app
          .post('/authentication')
          .set('cookie', 'XSRF-TOKEN=antani')
          .send(credentials)
          .expect(403)
          .end(function (err, res) {

            if (err) {
              return done(err);
            }

            validate_mandatory_headers(res.headers);

            done();
          });
      })
    })

    describe('POST /authentication', function () {
      it('responds 403 on valid wb login with missing XSRF token (missing cookie)', function (done) {
        var credentials = valid_login(i);
        app
          .post('/authentication')
          .set('X-XSRF-TOKEN', 'antani')
          .send(credentials)
          .expect(403)
          .end(function (err, res) {

            if (err) {
              return done(err);
            }

            validate_mandatory_headers(res.headers);

            done();
          });
      })
    })

    describe('POST /authentication', function () {
      it('responds 403 on valid wb login with missing XSRF token (header != cookie)', function (done) {
        var credentials = valid_login(i);
        app
          .post('/authentication')
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=notantani')
          .send(credentials)
          .expect(403)
          .end(function (err, res) {

            if (err) {
              return done(err);
            }

            validate_mandatory_headers(res.headers);

            done();
          });
      })
    })

    describe('POST /authentication', function () {
      it('responds 401 on invalid wb login (valid XSRF token)', function (done) {
        var credentials = invalid_login(i);
        app
          .post('/authentication')
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=antani')
          .send(credentials)
          .expect(401)
          .end(function (err, res) {

            if (err) {
              return done(err);
            }

            validate_mandatory_headers(res.headers);

            done();
          });
      })
    })

    describe('POST /authentication', function () {
      it('responds 200 on valid wb login (valid XSRF token)', function (done) {
        var credentials = valid_login(i);
        app
          .post('/authentication')
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=antani')
          .send(credentials)
          .expect(200)
          .end(function (err, res) {

            if (err) {
              return done(err);
            }

            validate_mandatory_headers(res.headers);

            done();
          });
      })
    })

  })(i);
}

for (var i=1; i<submission_population_order; i++){
  (function (i) {
    describe('POST /authentication', function () {
      it('responds 200 on valid wb login (valid XSRF token)', function (done) {
        var credentials = valid_login(i);
        app
          .post('/authentication')
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=antani')
          .send(credentials)
          .expect(200)
          .end(function (err, res) {

            if (err) {
              return done(err);
            }

            validate_mandatory_headers(res.headers);

            done();
          });
      })
    })

  })(i);
}
