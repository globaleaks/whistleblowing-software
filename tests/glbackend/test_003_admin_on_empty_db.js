/*
 This set of UT validate request/responses
 against authenticated admion resources on empty db.
 */

var request = require('supertest'),
  should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var authentication;

var invalid_admin_login = {
  "username": "admin",
  "password": "antani",
  "role": "admin"
}

var valid_admin_login = {
  "username": "admin",
  "password": "globaleaks",
  "role": "admin"
}

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
    'status_DELETE': 405,
  },
  {
    'url': '/admin/context',
    'status_GET': 200,
    'status_POST': 406,
    'status_PUT': 405,
    'status_DELETE': 405,
  },
  {
    'url': '/admin/receiver',
    'status_GET': 200,
    'status_POST': 406,
    'status_PUT': 405,
    'status_DELETE': 405,
  },
  {
    'url': '/admin/notification',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 406,
    'status_DELETE': 405,
  },
  {
    'url': '/admin/staticfiles',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 405,
    'status_DELETE': 405,
  },
  {
    'url': '/admin/overview/users',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 405,
    'status_DELETE': 405,
  },
  {
    'url': '/admin/overview/files',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 405,
    'status_DELETE': 405,
  },
  {
    'url': '/admin/overview/tips',
    'status_GET': 200,
    'status_POST': 405,
    'status_PUT': 405,
    'status_DELETE': 405,
  }
]

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

admin_resources.forEach(function (req) {
  describe('GET ' + req['url'], function () {
    it('responds 200 on GET ' + req['url'] + ' (authenticated)', function (done) {
      app
        .get(req['url'])
        .set('X-XSRF-TOKEN', 'antani')
        .set('cookie', 'XSRF-TOKEN=antani')
        .set('X-Session', authentication['session_id'])
        .expect(200)
        .end(function (err, res) {

          if (err) {
            return done(err);
          }

          validate_mandatory_headers(res.headers);

          done();
        });
    })
  })
})

admin_resources.forEach(function (req) {
  describe('POST ' + req['url'], function () {
    it('responds ' + req['status_POST'] + ' on POST ' + req['url'] + ' (authenticated, no content)', function (done) {
      app
        .post(req['url'])
        .set('X-XSRF-TOKEN', 'antani')
        .set('cookie', 'XSRF-TOKEN=antani')
        .set('X-Session', authentication['session_id'])
        .expect(req['status_POST'])
        .end(function (err, res) {

          if (err) {
            return done(err);
          }

          validate_mandatory_headers(res.headers);

          done();
        });
    })
  })
})

admin_resources.forEach(function (req) {
  describe('PUT ' + req['url'], function () {
    it('responds ' + req['status_PUT'] + ' on PUT ' + req['url'] + ' (authenticated, no content)', function (done) {
      app
        .put(req['url'])
        .set('X-XSRF-TOKEN', 'antani')
        .set('cookie', 'XSRF-TOKEN=antani')
        .set('X-Session', authentication['session_id'])
        .expect(req['status_PUT'])
        .end(function (err, res) {

          if (err) {
            return done(err);
          }

          validate_mandatory_headers(res.headers);

          done();
        });
    })
  })
})

admin_resources.forEach(function (req) {
  describe('DELETE ' + req['url'], function () {
    it('responds ' + req['status_DELETE'] + ' on DELETE ' + req['url'] + ' (authenticated)', function (done) {
      app
        .del(req['url'])
        .set('X-XSRF-TOKEN', 'antani')
        .set('cookie', 'XSRF-TOKEN=antani')
        .set('X-Session', authentication['session_id'])
        .expect(req['status_DELETE'])
        .end(function (err, res) {

          if (err) {
            return done(err);
          }

          validate_mandatory_headers(res.headers);

          done();
        });
    })
  })
})