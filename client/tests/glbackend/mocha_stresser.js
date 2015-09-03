/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest'),
  should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var contexts = [];

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

describe('Iteration...', function(){
  it(' Getting Context(s)', function(done){
    app
      .get('/contexts')
      .expect('Content-Type', 'application/json')
      .expect(200)
      .end(function(err, res) {
        if (err) {
          return done(err);
        } else {

          submission_number = 150;
          /* is not a .push because is already a list */
          contexts = res.body;
          console.log("Generating " + contexts.length * submission_number + " submissions...");

          for (i=0; i < contexts.length ; i++) {

            for(k = 0; k < submission_number ; k++ ) {

                  var new_submission = {};
                  new_submission.context_id = contexts[i].id;
                  new_submission.receivers = contexts[i].receivers;
                  new_submission.answers = {};
                  new_submission.graph_captcha_answer = "unicode";
                  new_submission.human_captcha_answer = 0;
                  new_submission.proof_of_work = 0;

                  app
                    .post('/submission')
                    .send(new_submission)
                    .expect('Content-Type', 'application/json')
                    .expect(201)
                    .end(function(err, res) {
                      if (err) {
                        return done(err);
                      } else {

                        var token = res.body;
                        /* here get implemented
                        some random file upload

                         Accept-Language: en-US,en;q=0.5
                         Accept-Encoding: gzip, deflate
                         DNT: 1
                         GL-Language: en
                         Content-Length: 1276
                         Content-Type: multipart/form-data; boundary=---------------------------9469237647089023971398185979
                         Connection: keep-alive
                         Pragma: no-cache
                         Cache-Control: no-cache

                         console.log(fileupbody);

                        */

                        /* and submission get completed here */

                        /*
                        var boundary = '---------------------------1111111111111111111111111111';
                        var fileupload = "";
                        app
                          .put('/submission/' + token.token_id + '/file')
                          .set('Content-Type', 'multipart/form-data; boundary=---------------------------1111111111111111111111111111')
                        */

                        validate_mandatory_headers(res.headers);

                        var sbms = {};
                        if (token.human_captcha !== false) {
                            var xx = Number(token.human_captcha.charAt(0)) + Number(token.human_captcha.charAt(4));
                            sbms.human_captcha_answer = xx;
                        }
                        else {
                            sbms.human_captcha_answer = 0;
                            console.log("Normal");
                        }

                        // sbms.graph_captcha = false;

                        sbms.context_id = token.context_id;
                        sbms.proof_of_work = 0;
                        sbms.graph_captcha_answer = 'unicode';
                        sbms.wb_steps = [];
                        sbms.answers = {};
                        sbms.receivers = contexts[(i-1)].receivers;

                        app
                          .put('/submission/' + token.token_id)
                          .send(sbms)
                          .set('Gl-Language', 'en')
                          .expect('Content-Type', 'application/json')
                          .expect(202)
                          .end(function(err, res) {
                            if (err) {
                              console.log("Error triggered, check the logs " + err);
                              return done(err);
                            } else {
                              console.log("Submission done, receipt: " +  res.body.receipt);
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



