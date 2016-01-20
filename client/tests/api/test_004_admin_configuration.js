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
  'username': 'admin',
  'password': 'globaleaks'
}

var user = {
  id: '',
  role: 'receiver',
  username: '',
  name: '',
  timezone: 0,
  language: 'en',
  description: '',
  pgp_key_public: '',
  pgp_key_expiration: '',
  pgp_key_fingerprint: '',
  pgp_key_info: '',
  pgp_key_remove: false,
  pgp_key_status: 'ignored',
  mail_address: 'receiver1@antani.gov', // used 'Recipient N' for population
  password: 'ringobongos3cur1ty',
  old_password: '',
  password_change_needed: false,
  state: 'enabled',
  deletable: 'true'
}

var fields = [
  {
    id: '',
    instance: 'instance',
    template_id: '',
    step_id: '',
    fieldgroup_id: '',
    label: 'Question 1',
    type: 'inputbox',
    preview: false,
    description: 'description',
    hint: 'field hint',
    multi_entry: false,
    multi_entry_hint: '',
    stats_enabled: false,
    required: true,
    attrs: {},
    options: [],
    children: [],
    y: 1,
    x: 0,
    width: 0
  },
  {
    id: '',
    instance: 'instance',
    template_id: '',
    step_id: '',
    fieldgroup_id: '',
    label: 'Question 2',
    type: 'inputbox',
    preview: false,
    description: 'description',
    hint: 'field hint',
    multi_entry: false,
    multi_entry_hint: '',
    stats_enabled: false,
    required: false,
    attrs: {},
    options: [],
    children: [],
    y: 2,
    x: 0,
    width: 0
  },
  {
    id: '',
    instance: 'instance',
    template_id: '',
    step_id: '',
    fieldgroup_id: '',
    label: 'Question 3',
    type: 'inputbox',
    preview: false,
    description: 'description',
    hint: 'field hint',
    multi_entry: false,
    multi_entry_hint: '',
    stats_enabled: false,
    required: false,
    attrs: {},
    options: [],
    children: [],
    y: 3,
    x: 0,
    width: 0
  }
]

var context = {
  id: '',
  name: 'Context 1',
  description: '',
  presentation_order: 0,
  tip_timetolive: 15,
  can_postpone_expiration: false,
  can_delete_submission: true,
  show_context: true,
  show_recipients_details: true,
  allow_recipients_selection: true,
  show_small_cards: false,
  enable_comments: true,
  enable_messages: true,
  enable_two_way_comments: true,
  enable_two_way_messages: true,
  enable_attachments: true,
  select_all_receivers: true,
  show_receivers_in_alphabetical_order: false,
  questionnaire_layout: 'horizontal',
  reset_questionnaire: true,
  maximum_selectable_receivers:0,
  receivers: [],
  custodians: [],
  steps: []
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
  it('responds 200 on valid admin login', function (done) {
    app
      .post('/authentication')
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
        node['languages_enabled'] = ['en', 'it'];
        node['enable_proof_of_work'] = false;
        node['tor2web_whistleblower'] = true;

        done();
      });
  })
})

describe('PUT /admin/node', function () {
  it('responds 202 on PUT /admin/node (allow_unencrypted, valid configuration)', function (done) {
    app
      .put('/admin/node')
      .send(node)
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

// we popolate population_order receivers
for (var i=0; i<population_order; i++) {
  (function (i) {
    describe('POST /admin/users', function () {
      it('responds 201 on POST /admin/users ' + i + ' (authenticated, valid new  receiver)', function (done) {
        var newObject = JSON.parse(JSON.stringify(user));
        newObject.username = 'Receiver ' + i;
        newObject.name = 'Receiver ' + i;
        newObject.mail_address = 'receiver' + i + '@antani.gov';

        app
          .post('/admin/users')
          .send(newObject)
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
  })(i);
}

// we popolate population_order contexts
for (var i=0; i<population_order; i++) {
  (function (i) {
    describe('POST /admin/contexts', function () {
      it('responds 201 on POST /admin/contexts ' + i + ' (authenticated, valid context)', function (done) {
        var newObject = JSON.parse(JSON.stringify(context));
        newObject.name = 'Context' + i + ' (selectable receivers: TRUE)';
        newObject.description = 'description of Context' + i;
        newObject.presentation_order = i;
        newObject.receivers = receivers_ids;

        app
          .post('/admin/contexts')
          .send(newObject)
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
  })(i);
}
