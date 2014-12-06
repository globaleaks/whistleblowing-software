/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest'),
    should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var population_order = 4;

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

var fields = [
  {
    id: '',
    is_template: false,
    step_id: '',
    fieldgroup_id: '',
    label: 'Field 1',
    type: 'inputbox',
    preview: false,
    description: 'field description',
    hint: 'field hint',
    multi_entry: false,
    stats_enabled: false,
    required: true,
    children: {},
    options: [],
    y: 2,
    x: 0
  },
  {
    id: '',
    is_template: false,
    step_id: '',
    fieldgroup_id: '',
    label: 'Field 2',
    type: 'inputbox',
    preview: false,
    description: 'description',
    hint: 'field hint',
    multi_entry: false,
    stats_enabled: false,
    required: false,
    children: {},
    options: [],
    y: 3,
    x: 0
  },
  {
    id: '',
    is_template: false,
    step_id: '',
    fieldgroup_id: '',
    label: 'Field 2',
    type: 'inputbox',
    preview: false,
    description: 'description',
    hint: 'field hint',
    multi_entry: false,
    stats_enabled: false,
    required: false,
    children: {},
    options: [],
    y: 3,
    x: 0
  },
  {
    id: '',
    is_template: false,
    step_id: '',
    fieldgroup_id: '',
    label: 'Generalities',
    type: 'fieldgroup',
    preview: false,
    description: 'field description',
    hint: 'field hint',
    multi_entry: false,
    stats_enabled: false,
    required: false,
    children: {},
    options: [],
    y: 4,
    x: 0
  },
  {
    id: '',
    is_template: false,
    step_id: '',
    fieldgroup_id: '',
    label: 'Name',
    type: 'inputbox',
    preview: false,
    description: 'field description',
    hint: 'field hint',
    multi_entry: false,
    stats_enabled: false,
    required: false,
    children: {},
    options: [],
    y: 0,
    x: 0
  },
  {
    id: '',
    is_template: false,
    step_id: '',
    fieldgroup_id: '',
    label: 'Surname',
    type: 'inputbox',
    preview: false,
    description: 'field description',
    hint: 'field hint',
    multi_entry: false,
    stats_enabled: false,
    required: false,
    children: {},
    options: [],
    y: 0,
    x: 0
  }
]

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
  "show_receivers":true,
  "enable_private_messages":true,
  "submission_timetolive":1, 
  "file_max_download":3,
  "select_all_receivers":true,
  "description":"XXXXX ħ ÐÐ",
  "tags":[],
  "selectable_receiver":false,
  "require_file_description":false,
  "name":"Context 1",
  "steps":[
     {
       'label': 'Step 1',
       'description': 'Step Description',
       'hint': 'Step Hint',
       'children': {}
     },
     {
       'label': 'Step 2',
       'description': 'Step Description',
       'hint': 'Step Hint',
       'children': {}
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
      newObject.selectable_receiver = true;

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
        newObject.password = newObject.mail_address;
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

// we popolate population_order/2 contexts
describe('POST /admin/context', function () {
  for (var i=population_order/2; i<population_order; i++) {
    (function (i) {
      it('responds 201 on POST /admin/context ' + i + ' (authenticated, valid context)', function (done) {
        var newObject = JSON.parse(JSON.stringify(context));
        newObject.name = 'Context ' + i ;
        newObject.presentation_order = i;
        newObject.name = 'Context ' + i + ' (selectable receivers: TRUE)';
        newObject.receivers = receivers_ids;
        newObject.selectable_receiver = true;

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
            newObject.step_id = contexts[i]['steps'][0]['id']

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
