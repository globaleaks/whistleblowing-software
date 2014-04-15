/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest'),
    should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var population_order = 42;

var receivers = new Array();
var receivers_ids = new Array();
var contexts = new Array();
var contexts_ids = new Array();
var contexts_list = new Array();

var authentication;
var node;

var valid_admin_login = {
  "username": "admin",
  "password": "globaleaks",
  "role": "admin"
}

var receiver = {
  can_delete_submission: false,
  comment_notification: false,
  contexts: [],
  description: "",
  file_notification: false,
  gpg_enable_files: false,
  gpg_enable_notification: false,
  gpg_key_armor: "",
  gpg_key_fingerprint: "",
  gpg_key_info: "",
  gpg_key_remove: false,
  gpg_key_status: "ignored",
  mail_address: "receiver1@antani.gov", // used 'Receiver N' for population
  message_notification: false,
  name: "receiver1@antani.gov", // used 'receiverN@antani.gov' for population
  password: "receiver1@antani.gov", // used 'receiverN@antani.gov' for population
  postpone_superpower: true,
  presentation_order: 0,
  receiver_level: 1,
  tags: [],
  tip_notification: false,
}

var context = {
  "receiver_introduction":"foca",
  "presentation_order":0,
  "postpone_superpower":false,
  "delete_consensus_percentage":0,
  "require_pgp":false,
  "receipt_regexp":"[0-9]{10}",
  "tip_timetolive":15, 
  "escalation_threshold":0,
  "can_delete_submission":true,
  "show_small_cards":false,
  "submission_timetolive":1, 
  "file_max_download":3,
  "select_all_receivers":true,
  "description":"XXXXX ħ ÐÐ",
  "tags":[],
  "selectable_receiver":false,
  "require_file_description":false,
  "name":"Context 1",
  "fields":[
    {
      "name":"first",
      "hint":"the first",
      "required":true,
      "presentation_order":1,
      "value":"",
      "key":"",
      "preview":true,
      "type":"text"
    },
    {
      "name":"second",
      "hint":"the second",
      "required":true,
      "presentation_order":2,
      "value":"",
      "key":"",
      "preview":true,
      "type":"radio",
      "options": [
        {
          "order":0,
          "value":"a",
          "name":"a"
        },
        {
          "order":0,
          "value":"b",
          "name":"b"
        },
        {
          "order":0,
          "value":"c",
          "name":"c"
        }
      ]
    },
    {
      "name":"third",
      "hint":"the third",
      "required":true,
      "presentation_order":3,
      "value":"",
      "key":"",
      "preview":true,
      "type":"select",
      "options": [
        {
          "order":0,
          "value":"a",
          "name":"the 4th do not exist"
        },
        {
          "order":0,
          "value":"b",
          "name":"il 4° non esiste"
	},
        {
          "order":0,
          "value":"c",
          "name":"blah"
        }
      ]
    },
    {
      "name":"fifth",
      "hint":"teh 5th",
      "required":true,
      "presentation_order":5,
      "value":"",
      "key":"",
      "preview":true,
      "type":"checkboxes",
      "options":
        [
          {
            "order":0,
            "value":"a",
            "name":"a"
          },
          {
            "order":0,
            "value":"b",
            "name":"b"
	  },
          {
            "order":0,
            "value":"c",
            "name":"c"
          },
          {
            "order":0,
            "value":"d",
            "name":"d"
          }
        ]
    },
    {
      "name":"sixth",
      "hint":"666 number of the beast!",
      "required":true,
      "presentation_order":6,
      "value":"",
      "key":"",
      "preview":true,
      "type":"textarea"
    },
    {
      "name":"seventh",
      "hint":"seven figthers! (it's a number!)",
      "required":true,
      "presentation_order":7,
      "value":"123",
      "key":"",
      "preview":true,
      "type":"number"
    },
    {
      "name":"eighth",
      "hint":"eighththththth (url)",
      "required":true,
      "presentation_order":0,
      "value":"https://globaleaks.org",
      "key":"",
      "preview":true,
      "type":"url"
    },
    {
      "name":"nineth",
      "hint":"nine hell (phone)",
      "required":true,
      "presentation_order":8,
      "value":"+3933932143413",
      "key":"",
      "preview":true,
      "type":"phone"
    },
    {
      "name":"tenth",
      "hint":"the 10th in english (email)",
      "presentation_order":9,
      "required":true,
      "value":"email@domain.tld",
      "key":"",
      "preview":true,
      "type":"email"
    }
  ],
  "file_required":false,
  "maximum_selectable_receivers":0,
  "tip_max_access":500,
  "fields_introduction":"something",
  "receivers": []
}

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
        node['password'] = '';
        node['old_password'] = '';
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

// we popolate population_order contexts
for (var i=0; i<population_order / 2; i++) {
  describe('POST /admin/context', function () {

    var newObject = JSON.parse(JSON.stringify(context));
    newObject.name = 'Context ' + i ;
    newObject.presentation_order = i;
    newObject.name = 'Context ' + i + ' (selectable receivers: TRUE)';
    newObject.selectable_receiver = true;

    it('responds 201 on POST /admin/context (authenticated, valid context[' + i + '])', function (done) {
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
for (var i=0; i<population_order; i++) {
  describe('POST /admin/receiver', function () {

    var newObject = JSON.parse(JSON.stringify(receiver));
    newObject.mail_address = 'receiver' + i + '@antani.gov';
    newObject.password = newObject.mail_address;
    newObject.name = 'Receiver ' + i;
    newObject.contexts = contexts_ids;
    newObject.presentation_order = i;

    it('responds 201 on POST /admin/receiver (authenticated, valid receiver[' + i + '])', function (done) {
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
  })
}

// we popolate population_order/2 contexts
for (var i=population_order/2; i<population_order; i++) {
  describe('POST /admin/context', function () {

    var newObject = JSON.parse(JSON.stringify(context));
    newObject.name = 'Context ' + i;
    newObject.receivers = receivers_ids;
    newObject.presentation_order = i;
    newObject.name = 'Context ' + i + ' (selectable receivers: FALSE)';
    newObject.selectable_receiver = false;

    it('responds 201 on POST /admin/context (authenticated, valid context[' + i + '])', function (done) {
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
