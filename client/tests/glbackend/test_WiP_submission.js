/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest'),
  should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var receivers, receivers_ids;
var contexts, contexts_ids;

var tokens = [];
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
    if (headers[key.toLowerCase()] != mandatory_headers[key]) {
      throw key + ' != ' + mandatory_headers[key];
    }
  }
};

describe('GET /contexts', function(){
  it(' Getting Context(s)', function(done){
    app
      .get('/contexts')
      .expect('Content-Type', 'application/json')
      .expect(200)
      .end(function(err, res) {
        if (err) {
          return done(err);
        } else {

          validate_mandatory_headers(res.headers);

          /* is not a .push because is already a list */
          contexts = res.body;

          for (var i=0; i < contexts.length; i++) {
            contexts_ids.push(contexts[i].id);
          }
          console.log("C " + contexts_ids);
          done();
        }
      });
  })
});

describe('GET /receivers', function(){
  it(' Getting Receiver(s)', function(done){
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
            throw '/receivers didn\'t return ' + population_order + ' receivers';
          }

          receivers = res.body;

          for (var i=0; i<population_order; i++) {

            receivers_ids.push(receivers[i].id);

            if(receivers[i].contexts.length != population_order) {
              throw '/receivers didn\'t return ' + population_order + ' receivers associated to each receiver';
            }
          }

          done();
        }
      });
  })
});


describe('POST /submission', function(){
  for (var x = 0; x < 1 ; x++)
  {
      for (var i=0; i<submission_population_order; i++) {
        (function (i) {
          it('responds with ', function(done){

            var new_submission = {};
            new_submission.context_id = contexts_ids[i];
            console.log(i);
            console.log(contexts_ids[i]);
            // new_submission.receivers = receivers_ids;
            //new_submission.wb_steps = [];
            //new_submission.human_captcha_answer = 0;

            /* new_submission.wb_steps = fill_steps(contexts[i].steps); */

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

                  // console.log(res.headers);
                  console.log(res.body);
                  /* validate_mandatory_headers(res.headers); */
                  tokens.push(res.body);
                  console.log('and now');
                  console.log(tokens);

                  done();
                }
              });
          })
        })(i);
      }
  }
});

describe('PUT /submission', function(){
  console.log('aaaa xxxxx');
  for (i = 0; i < 1; i++) {
    (function(i) {
      it('responds with ', function(done) {

        var sbms = {};
        // sbms.graph_captcha = false;
        sbms.context_id = tokens[i].context_id;
        sbms.human_captcha_answer = 0;
        sbms.wb_steps = [];
        sbms.receivers = ["0870e71a-7024-4583-b67e-56090eccd634"];
        console.log(receivers_ids);

        app
          .put('/submission/' + tokens[i].id)
          .send(sbms)
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=antani')
          .expect('Content-Type', 'application/json')
          .expect(201)
          .end(function(err, res) {
            if (err) {
              return done(err);
            } else {
              done();
            }
          });

      })

    })(i)
  }

});
