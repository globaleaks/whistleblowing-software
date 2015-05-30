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


var fill_field_recursively = function(field) {
    field['value'] = 'antani ¹²³ ';
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


describe('doing a shitload of submission', function(){

  this.timeout(10000);

  it(' really ', function(done){
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

            dummy_steps_filled = fill_steps(contexts[i].steps);
            context_id_copy = contexts[i].id;
            receiver_list = contexts[i].receivers;

            for(k = 0; k < 16; k++ ) {

                  subm_req = {};
                  subm_req.context_id = context_id_copy;

                  app
                    .post('/submission')
                    .send(subm_req)
                    .set('X-XSRF-TOKEN', 'antani')
                    .set('cookie', 'XSRF-TOKEN=antani')
                    .expect('Content-Type', 'application/json')
                    .expect(201)
                    .end(function(err, tokenfull) {
                      if (err) {
                        return done(err);
                      } else {

                        validate_mandatory_headers(tokenfull.headers); 

                        sbms = {};
                        // sbms.graph_captcha = false;
                        sbms.context_id = context_id_copy;
                        sbms.human_captcha_answer = 0;
                        sbms.wb_steps = dummy_steps_filled;
                        sbms.receivers = receiver_list;

                        app
                          .put('/submission/' + tokenfull.body.id)
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
                              validate_mandatory_headers(res.headers); 
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



