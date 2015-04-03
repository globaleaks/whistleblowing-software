/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest'),
    should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var population_order = 15;

var receivers = new Array();
var receivers_ids = new Array();
var contexts = new Array();
var contexts_ids = new Array();
var fields = new Array();
var fields_ids = new Array();

var authentication;
var node;

var valid_admin_login = {
  "username": "admin",
  /* default password cdscds */
  "password": "Antani1234",
  "role": "admin"
}

var receiver = {
  "password":"Antani1234",
  "contexts":[],
  "description":"",
  "mail_address":"ciao@ciao.it",
  "ping_mail_address":"",
  "can_delete_submission":false,
  "postpone_superpower":false,
  "tip_notification":true,
  "ping_notification":false,
  "pgp_key_info":"",
  "pgp_key_fingerprint":"",
  "pgp_key_remove":false,
  "pgp_key_public":"",
  "pgp_key_expiration":"",
  "pgp_key_status":"ignored",
  "pgp_enable_notification":false,
  "pgp_e2e_public":"",
  "pgp_e2e_private":"",
  "presentation_order":0,
  "state":"enable",
  "configuration":"default",
  "password_change_needed":true,
  "language":"en",
  "timezone":"0",
  "name":"FOCA"
}

context = {
  "name":"AAAAAAAA",
  "description":"",
  "steps":[],
  "receivers":[],
  "select_all_receivers":false,
  "tip_timetolive":15,
  "receiver_introduction":"",
  "postpone_superpower":false,
  "can_delete_submission":false,
  "maximum_selectable_receivers":0,
  "show_small_cards":false,
  "show_receivers":true,
  "enable_private_messages":true,
  "presentation_order":0
>>>>>>> bug hunting + restored mocha
}

var validate_mandatory_headers = function(headers) {
  var mandatory_headers = {
    'X-XSS-Protection': '1; mode=block',
    'X-Robots-Tag': 'noindex',
    'X-Content-Type-Options': 'nosniff',
    'Expires': '-1',
    'Server': 'globaleaks',
    'Pragma':  'no-cache',
    'Cache-control': 'no-cache, no-store, must-revalidate'
  }

  for (var key in mandatory_headers) {
    if (headers[key.toLowerCase()] != mandatory_headers[key]) {
      throw key + ' != ' + mandatory_headers[key];
    }
  }
}

describe('POST /authentication', function () {
  it('responds 200 on valid admin login (valid XSRF token)', function (done) {
    app
      .post('/authentication')
      .set('X-XSRF-TOKEN', 'antani')
      .set('cookie', 'XSRF-TOKEN=antani')
      .send(valid_admin_login)
      .expect(200)
      .end(function (err, res) {

        if (err) {
          return done(err);
        }

        validate_mandatory_headers(res.headers);

        authentication = res.body;

        done();
      });
  })
})

describe('GET /admin/node', function () {
  it('responds 200 on GET /admin/node', function (done) {
    app
      .get('/admin/node')
      .set('X-XSRF-TOKEN', 'antani')
      .set('cookie', 'XSRF-TOKEN=antani')
      .set('X-Session', authentication['session_id'])
      .expect(200)
      .end(function (err, res) {

        if (err) {
          return done(err);
        }

        validate_mandatory_headers(res.headers);

        node = JSON.parse(JSON.stringify(res.body));

        /* adding various keys needed next POST */
        node['allow_unencrypted'] = true;

        done();
      });
  })
})

describe('PUT /admin/node', function () {
  it('responds 202 on PUT /admin/node (allow_unencrypted, valid configuration)', function (done) {
    app
      .put('/admin/node')
      .send(node)
      .set('X-XSRF-TOKEN', 'antani')
      .set('cookie', 'XSRF-TOKEN=antani')
      .set('X-Session', authentication['session_id'])
      .expect(202)
      .end(function (err, res) {

        if (err) {
          return done(err);
        }

        validate_mandatory_headers(res.headers);

        done();
      });
  })
})

// we popolate population_order/2 contexts
for (var i=0; i<population_order / 2; i++) {
  describe('POST /admin/context', function () {
    it('responds 201 on POST /admin/context ' + i + ' (authenticated, valid context)', function (done) {

      var newObject = JSON.parse(JSON.stringify(context));
      newObject.name = 'Context ' + i;
      newObject.presentation_order = i;
      newObject.name = 'Context ' + i + ' (selectable receivers: TRUE)';

      app
        .post('/admin/context')
        .send(newObject)
        .set('X-XSRF-TOKEN', 'antani')
        .set('cookie', 'XSRF-TOKEN=antani')
        .set('X-Session', authentication['session_id'])
        .expect(201)
        .end(function (err, res) {

          if (err) {
            return done(err);
          }

          validate_mandatory_headers(res.headers);

          contexts.push(res.body);

          contexts_ids.push(res.body.id);

          done();

        });
    })
  })
}

// we popolate population_order receivers
describe('POST /admin/receiver', function () {
  for (var i=0; i<population_order; i++) {
    (function (i) {
      it('responds 201 on POST /admin/receiver ' + i + ' (authenticated, valid receiver)', function (done) {

        var newObject = JSON.parse(JSON.stringify(receiver));
        newObject.mail_address = 'receiver' + i + '@antani.gov';
        newObject.name = 'Receiver ' + i;
        newObject.contexts = contexts_ids;
        newObject.presentation_order = i;

        app
          .post('/admin/receiver')
          .send(newObject)
          .set('X-XSRF-TOKEN', 'antani')
          .set('cookie', 'XSRF-TOKEN=antani')
          .set('X-Session', authentication['session_id'])
          .expect(201)
          .end(function (err, res) {

            if (err) {
              return done(err);
            }

            validate_mandatory_headers(res.headers);

            receivers.push(res.body);

            receivers_ids.push(res.body.id);

            done();

        });
      })
    })(i);
  }
})

// we popolate fields for each context
describe('POST /admin/field', function () {
  for (var i=0; i<population_order; i++) {
    for (var j=0; j<fields.length; j++) {
      (function (i, j) {
        it('responds 201 on POST /admin/field, valid field', function (done) {

            var newObject = JSON.parse(JSON.stringify(fields[j]));
            newObject.step_id = contexts[i]['steps'][0]['id'];

            app
              .post('/admin/field')
              .send(newObject)
              .set('X-XSRF-TOKEN', 'antani')
              .set('cookie', 'XSRF-TOKEN=antani')
              .set('X-Session', authentication['session_id'])
              .expect(201)
              .end(function (err, res) {

                if (err) {
                  return done(err);
                }

                validate_mandatory_headers(res.headers);

                fields.push(res.body);

                fields_ids.push(res.body.id);

                done();

              });
        })
      })(i, j);
    }
  }
})
