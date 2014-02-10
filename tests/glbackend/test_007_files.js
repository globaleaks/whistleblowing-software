/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest'),
  should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var population_order = 4;

var submissions = new Array();
var files = new Array();
var context_id = new Array();


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

          if (res.body.length != population_order) {
            throw "/contexts didn't return " + population_order + " contexts";
          }

          contexts = res.body;

          for (var i=0; i<population_order; i++) {
            contexts_id.push(contexts[i].id);
          }

          done();
        }
      });
  })
})

describe('POST /submission', function(){
  for (var i=0; i<population_order; i++) {
    (function (i) {
      it('responds with ', function(done){

        var new_submission = { }

        contexts[i].fields.forEach(function (field) {
          new_submission.wb_fields[field.key]  = "primo";
        })

        new_submission.context_id = contexts_id[i];
        new_submission.files = [];
        new_submission.finalize = false;
        new_submission.receivers = [];

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

describe('POST /submission', function(){
  for (var i=0; i<population_order; i++) {
    (function (i) {
      it('responds with ', function(done){

        var new_file = {
	    name: "afilename.txt",
	    description: "a description haha",
	    size: 20,
	    content_type: "09876543211234567890",
	    date: "somethingignored?"
	}

        app
          .post('/submission/' + submissions[i].id + '/file')
          .send(new_file)
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=antani')
          .expect('Content-Type', 'application/json')
          .expect(201)
          .end(function(err, res) {
            if (err) {
              return done(err);
            } else {

              validate_mandatory_headers(res.headers);

              files.push(res.body);

              done();
            }
          });

      })
    })(i);
  }
})


describe('POST /submission', function(){
  for (var i=0; i<population_order; i++) {
    (function (i) {

      it('responds with ', function(done){

        submissions[i].wb_fields = {};

        contexts[i].fields.forEach(function (field) {
          submissions[i].wb_fields[field.key]  = "antani";
        })

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

              wb_receipts.push(res.body.receipt);

              done();
            }
          });

      })
    })(i);
  }
})
