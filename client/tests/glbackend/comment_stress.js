/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest');

var host = 'http://127.0.0.1:8082';

var app = request(host);

describe('COMMENT -- hardcoded receipt', function(){
  it(' COMMENT spam -- hardcoded receipt', function(done){
    var auth_wb = {"receipt": "3508607111818246"};
    app
        .post ('/receiptauth')
        .send(auth_wb)
        .expect ('Content-Type', 'application/json')
        .expect (200)
        .end (function (err, res) {
          if (err) {
            return done(err);
          } else {
            console.log(res.body.session_id);

            for(var i = 0; i < 100; i++) {
              var comment_content = {"content":"AUTOMATIC COMMENT VIA comment_stress.js"};

              app
                 .post('/wbtip/comments')
                      .set('X-Session',res.body.session_id)
                      .send(comment_content)
                      .expect('Content-Type', 'application/json')
                      .expect(201)
                      .end(function(err, res) {
                        if (err) {
                          return done(err);
                        } else {
                            console.log("done " + i);
                        }
                      });
                      done();
            }
        }
      });
  });
});



