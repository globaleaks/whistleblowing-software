/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var population_order = 4;
var submission_population_order = 10;
var comments_population_order = 10;

var authentication;

var receivers = [];
var receivers_ids = [];
var contexts = [];
var contexts_ids = [];
var submissions = [];
var submission_tokens = [];
var wb_keycodes  = [];

var validate_mandatory_headers = function(headers) {
  var mandatory_headers = {
    'X-XSS-Protection': '1; mode=block',
    'X-Robots-Tag': 'noindex',
    'X-Content-Type-Options': 'nosniff',
    'Expires': '-1',
    'Server': 'globaleaks',
    'Pragma':  'no-cache',
    'Cache-control': 'no-cache, no-store, must-revalidate'
  };

  for (var key in mandatory_headers) {
    if (headers[key.toLowerCase()] !== mandatory_headers[key]) {
      throw key + ' != ' + mandatory_headers[key];
    }
  }
};

var valid_login = function(i) {
  return {
    'receipt': wb_keycodes[i]
  };
};

var invalid_login = function() {
  return {
    'receipt': 'antani'
  };
};

var fill_field_recursively = function(answers, field) {
  answers[field.id] = {'0': {'0': ''}};
  for (var i = 0; i < field.children.length; i++) {
    fill_field_recursively(field.children[i]);
  }
};

var fill_answers = function(steps) {
  var answers = {};
  for (var i in steps) {
    for (var c in steps[i].children) {
      fill_field_recursively(answers, steps[i].children[c]);
    }
  }

  return answers;
};

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

          if (res.body.length !== population_order) {
            throw '/contexts didn\'t return ' + population_order + ' contexts';
          }

          contexts = res.body;

          for (var i=0; i<population_order; i++) {
            contexts_ids.push(contexts[i].id);

            if(contexts[i].receivers.length !== population_order) {
              throw '/contexts didn\'t return ' + population_order + ' receivers associated to each context';
            }
          }

          done();
        }
      });
  });
});

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

          if (res.body.length !== population_order) {
            throw '/receivers didn\'t return ' + population_order + ' receivers';
          }

          receivers = res.body;

          for (var i=0; i<population_order; i++) {
            receivers_ids.push(receivers[i].id);

            if(receivers[i].contexts.length !== population_order) {
              throw '/receivers didn\'t return ' + population_order + ' contexts associated to each receiver';
            }
          }

          done();
        }
      });
  });
});

for (i=0; i<submission_population_order; i++) {
  (function () {
    describe('POST /token', function(){
      it('responds with ', function(done){
        var new_submission_token = {'type': 'submission'};
        app
          .post('/token')
          .send(new_submission_token)
          .expect('Content-Type', 'application/json')
          .expect(201)
          .end(function(err, res) {
            if (err) {
              return done(err);
            } else {

              validate_mandatory_headers(res.headers);
              submission_tokens.push(res.body);

              done();
            }
          });
      });
    });
  })();
}

for (i=0; i<submission_population_order; i++) {
  (function (i) {
    describe('PUT /token/token_id', function(){
      it('responds with ', function(done){
        if(submission_tokens[i].human_captcha) {
          app
            .put('/token/' + submission_tokens[i].id)
            .send(submission_tokens[i])
            .expect('Content-Type', 'application/json')
            .expect(202)
            .end(function(err, res) {
              if (err) {
                return done(err);
              } else {
                validate_mandatory_headers(res.headers);
                submission_tokens[i] = res.body;

                done();
              }
            });
        } else {
          done();
        }
      });
    });
  })(i);
}

for (i=0; i<submission_population_order; i++) {
  (function (i) {
    describe('PUT /submission/submission_id', function(){
      it('responds with ', function(done){
        var new_submission = {};
        new_submission.id = submission_tokens[i].id;
        new_submission.context_id = contexts_ids[0];
        new_submission.receivers = receivers_ids;
        new_submission.identity_provided = false;
        new_submission.answers = fill_answers(contexts[0].steps);
        new_submission.total_score = 0;

        app
          .put('/submission/' + submission_tokens[i].id)
          .send(new_submission)
          .expect('Content-Type', 'application/json')
          .expect(202)
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
      });
    });
  })(i);
}

describe('POST /receiptauth', function () {
  it('responds 401 on invalid wb login', function (done) {
    var credentials = invalid_login();
    app
      .post('/receiptauth')
      .send(credentials)
      .expect(401)
      .end(function (err, res) {
        if (err) {
          return done(err);
        }
        validate_mandatory_headers(res.headers);
        authentication = res.body;
        done();
      });
  });
});

describe('POST /receiptauth', function () {
  it('responds 200 on valid wb login', function (done) {
    var credentials = valid_login(0);
    app
      .post('/receiptauth')
      .send(credentials)
      .expect(200)
      .end(function (err, res) {
        if (err) {
          return done(err);
        }
        validate_mandatory_headers(res.headers);
        authentication = res.body;
        done();
      });
  });
});

for (var i=1; i<comments_population_order; i++) {
  (function () {
    describe('POST /wbtip/comments', function () {
      it('responds 201 on wb adding a comment on an existent submission', function (done) {
        app
          .post('/wbtip/comments')
          .send({"content": "COMMENT!"})
          .set('X-Session', authentication.session_id)
          .expect(201)
          .end(function (err, res) {
            if (err) {
              return done(err);
            }
            validate_mandatory_headers(res.headers);
            done();
          });
      });
    });
  })();
}
