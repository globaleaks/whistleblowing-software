/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest'),
  should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var contexts = [], contexts_ids = [];

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

          /* is not a .push because is already a list */
          contexts = res.body;

          for (var i=0; i < contexts.length; i++) {

            var tokens = [];

            for(k = 0; k < 30; k++ ) {

                  var new_submission = {};
                  new_submission.context_id = contexts[i].id;
                  var receivers_id = contexts[i].receivers;
                  // console.log(new_submission);
                  // console.log(contexts_ids[i]);

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
                        // console.log(res.body);
                        var token = res.body;
                        /* validate_mandatory_headers(res.headers); */

                        var sbms = {};
                        // sbms.graph_captcha = false;
                        sbms.context_id = new_submission.context_id;
                        sbms.human_captcha_answer = 0;
                        sbms.wb_steps = [];
                        sbms.receivers = receivers_id;
                        // console.log(receivers_ids);

                        app
                          .put('/submission/' + token.id)
                          .send(sbms)
                          .set('X-XSRF-TOKEN', 'antani')
                          .set('cookie', 'XSRF-TOKEN=antani')
                          .expect('Content-Type', 'application/json')
                          .expect(201)
                          .end(function(err, res) {
                            if (err) {
                              console.log("unhappy!");
                              return done(err);
                            } else {
                              console.log("happy!");
                              done();
                            }
                          });

                      }
                    });

            }

          }


        }
      });
  })
});



