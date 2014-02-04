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
var receivers_gus = new Array();
var contexts = new Array();
var contexts_gus = new Array();

var authentication;

var valid_admin_login = {
  "username": "admin",
  "password": "globaleaks",
  "role": "admin"
}

var receiver = {
  can_delete_submission: false,
  comment_notification: true,
  contexts: [],
  description: "",
  file_notification: true,
  gpg_enable_files: false,
  gpg_enable_notification: false,
  gpg_key_armor: "",
  gpg_key_fingerprint: "",
  gpg_key_info: "",
  gpg_key_remove: false,
  gpg_key_status: "ignored",
  mail_address: "receiver1@antani.gov", // used 'Receiver N' for population
  message_notification: true,
  name: "receiver1@antani.gov", // used 'receiverN@antani.gov' for population
  password: "receiver1@antani.gov", // used 'receiverN@antani.gov' for population
  postpone_superpower: false,
  presentation_order: 0,
  receiver_level: 1,
  tags: [],
  tip_notification: true,
}

var context = {
  "receiver_introduction":"",
  "presentation_order":0,
  "postpone_superpower":false,
  "delete_consensus_percentage":0,
  "require_pgp":false,
  "receipt_regexp":"[0-9]{10}",
  "tip_timetolive":15,
  "escalation_threshold":0,
  "can_delete_submission":false,
  "show_small_cards":false,
  "submission_timetolive":48,
  "file_max_download":3,
  "select_all_receivers":true,
  "description":"",
  "tags":[],
  "selectable_receiver":true,
  "require_file_description":false,
  "name":"Context 1",
  "fields":[
    {
      "name":"1",
      "hint":"1",
      "required":true,
      "presentation_order":1,
      "value":"",
      "key":"",
      "preview":true,
      "type":"text"
    },
    {
      "name":"2",
      "hint":"2",
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
      "name":"3",
      "hint":"3",
      "required":true,
      "presentation_order":3
      ,"value":"",
      "key":"",
      "preview":true,
      "type":"select",
      "options": [
        {
          "order":0,
          "value":"a",
          "name":"a"
        },
        {
          "order":0,
          "value":"b",
          "name":"b"},
        {
          "order":0,
          "value":"c",
          "name":"c"
        }
      ]
    },
    {
      "name":"4",
      "hint":"4",
      "required":true,
      "presentation_order":4,
      "value":"",
      "key":"",
      "preview":true,
      "type":"multiple",
      "options": [
        {
          "order":0,
          "value": "a",
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
      "name":"5",
      "hint":"5",
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
      "name":"6",
      "hint":"6",
      "required":true,
      "presentation_order":6,
      "value":"",
      "key":"",
      "preview":true,
      "type":"textarea"
    },
    {"name":"7",
      "hint":"7",
      "required":true,
      "presentation_order":7,
      "value":"",
      "key":"",
      "preview":true,
      "type":"number"
    },
    {
      "name":"8",
      "hint":"8",
      "required":true,
      "presentation_order":0,
      "value":"",
      "key":"",
      "preview":true,
      "type":"url"
    },
    {
      "name":"9",
      "hint":"9",
      "required":true,
      "presentation_order":8,
      "value":"",
      "key":"",
      "preview":true,
      "type":"phone"
    },
    {
      "name":"10",
      "presentation_order":9,
      "hint":"10",
      "required":true,
      "value":"",
      "key":"",
      "preview":true,
      "type":"email"
    }
  ],
  "file_required":false,
  "maximum_selectable_receivers":0,
  "tip_max_access":500,
  "fields_introduction":"",
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

// we popolate population_order/2 contexts
for (var i=0; i<population_order/2; i++) {
  describe('POST /admin/context', function () {

    var newObject = JSON.parse(JSON.stringify(context));
    newObject.name = 'Context ' + i;
    newObject.presentation_order = i;

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

          contexts_gus.push(res.body.context_gus);

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
    newObject.contexts = contexts_gus;
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

          receivers_gus.push(res.body.receiver_gus);

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
    newObject.receivers = receivers_gus;
    newObject.presentation_order = i;

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

          contexts_gus.push(res.body.context_gus);

          done();
        });
    })
  })
}