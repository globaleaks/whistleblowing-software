/*
 This set of UT validate request/responses
 against authenticated admion resources on empty db.
 */

var request = require('supertest');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var utils = require('./utils.js');

var authentication;

/*
  The following is a list of all resources that has a
  fixed name and do not include variables in the url.
  For all these resources is possible to address the following tests:
     1) GET
     2) POST with missing payload
     3) PUT with missing payload
     4) DELETE

  (all the tests above are conducted on the initial db)
 */
var admin_resources = [
  {
    'url': '/admin/node',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 406,
    'status_DELETE': 405
  },
  {
    'url': '/admin/contexts',
    'status_GET': 200,
    'status_POST': 406,
    'status_PUT': 405,
    'status_DELETE': 405
  },
  {
    'url': '/admin/fields',
    'status_GET': 405,
    'status_POST': 406,
    'status_PUT': 405,
    'status_DELETE': 405
  },
  {
    'url': '/admin/fieldtemplates',
    'status_GET': 200,
    'status_POST': 406,
    'status_PUT': 405,
    'status_DELETE': 405
  },
  {
    'url': '/admin/users',
    'status_GET': 200,
    'status_POST': 406,
    'status_PUT': 405,
    'status_DELETE': 405
  },
  {
    'url': '/admin/receivers',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 405,
    'status_DELETE': 405
  },
  {
    'url': '/admin/notification',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 406,
    'status_DELETE': 405
  },
  {
    'url': '/admin/staticfiles',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 405,
    'status_DELETE': 405
  },
  {
    'url': '/admin/overview/users',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 405,
    'status_DELETE': 405
  },
  {
    'url': '/admin/overview/files',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 405,
    'status_DELETE': 405
  },
  {
    'url': '/admin/overview/tips',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 405,
    'status_DELETE': 405
  }
];

describe('POST /authentication', function () {
  it('responds 200 on valid admin login', function (done) {
    app
      .post('/authentication')
      .send(utils.valid_admin_login)
      .expect(200)
      .end(function (err, res) {
        if (err) {
          return done(err);
        }

        utils.validate_mandatory_headers(res.headers);

        authentication = res.body;

        done();
      });
  });
});

admin_resources.forEach(function (req) {
  describe('GET ' + req['url'], function () {
    it('responds ' + req['status_GET'] + ' on GET ' + req['url'] + ' (authenticated, no id)', function (done) {
      app
        .get(req['url'])
        .set('X-Session', authentication['session_id'])
        .expect(req['status_GET'])
        .end(function (err, res) {

          if (err) {
            return done(err);
          }

          utils.validate_mandatory_headers(res.headers);

          done();
        });
    });
  });
});

admin_resources.forEach(function (req) {
  describe('POST ' + req['url'], function () {
    it('responds ' + req['status_POST'] + ' on POST ' + req['url'] + ' (authenticated, no content)', function (done) {
      app
        .post(req['url'])
        .set('X-Session', authentication['session_id'])
        .expect(req['status_POST'])
        .end(function (err, res) {
          if (err) {
            return done(err);
          }

          utils.validate_mandatory_headers(res.headers);

          done();
        });
    });
  });
});

admin_resources.forEach(function (req) {
  describe('PUT ' + req['url'], function () {
    it('responds ' + req['status_PUT'] + ' on PUT ' + req['url'] + ' (authenticated, no content)', function (done) {
      app
        .put(req['url'])
        .set('X-Session', authentication['session_id'])
        .expect(req['status_PUT'])
        .end(function (err, res) {
          if (err) {
            return done(err);
          }

          utils.validate_mandatory_headers(res.headers);

          done();
        });
    });
  });
});

admin_resources.forEach(function (req) {
  describe('DELETE ' + req['url'], function () {
    it('responds ' + req['status_DELETE'] + ' on DELETE ' + req['url'] + ' (authenticated, no id)', function (done) {
      app
        .del(req['url'])
        .set('X-Session', authentication['session_id'])
        .expect(req['status_DELETE'])
        .end(function (err, res) {
          if (err) {
            return done(err);
          }

          utils.validate_mandatory_headers(res.headers);

          done();
        });
    });
  });
});
