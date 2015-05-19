/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest'),
  should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var authentication;
var valid_login;
var invalid_login = {
  'username': 'invalid',
  'password': 'login',
  'role': 'receiver'
}

var population_order = 3;

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

describe('GET /receivers', function () {
  it('responds 200 on GET /receivers', function (done) {
    app
      .get('/receivers')
      .set('X-XSRF-TOKEN', 'antani')
      .set('cookie', 'XSRF-TOKEN=antani')
      .expect(200)
      .end(function (err, res) {

        if (err) {
          return done(err);
        }

        validate_mandatory_headers(res.headers);

        receiver_id = JSON.parse(JSON.stringify(res.body))[0]['id'];

        valid_login = {
          'username': receiver_id,
          'password': 'ringobongos3cur1ty',
          'role': 'receiver'
        }

        done();
      });
  })
})

describe('POST /authentication', function () {
  it('responds 403 on valid login with missing XSRF token (missing header)', function (done) {
    app
      .post('/authentication')
      .set('cookie', 'XSRF-TOKEN=antani')
      .send(valid_login)
      .expect(403)
      .end(function (err, res) {

        if (err) {
          return done(err);
        }

        validate_mandatory_headers(res.headers);

        done();
      });
  })
})

describe('POST /authentication', function () {
  it('responds 403 on valid login with missing XSRF token (missing cookie)', function (done) {
    app
      .post('/authentication')
      .set('X-XSRF-TOKEN', 'antani')
      .send(valid_login)
      .expect(403)
      .end(function (err, res) {

        if (err) {
          return done(err);
        }

        validate_mandatory_headers(res.headers);

        done();
      });
  })
})

describe('POST /authentication', function () {
  it('responds 403 on valid login with missing XSRF token (header != cookie)', function (done) {
    app
      .post('/authentication')
      .set('X-XSRF-TOKEN', 'antani')
      .set('cookie', 'XSRF-TOKEN=notantani')
      .send(valid_login)
      .expect(403)
      .end(function (err, res) {

        if (err) {
          return done(err);
        }

        validate_mandatory_headers(res.headers);

        done();
      });
  })
})

describe('POST /authentication', function () {
  it('responds 401 on invalid login (valid XSRF token)', function (done) {
    app
      .post('/authentication')
      .set('X-XSRF-TOKEN', 'antani')
      .set('cookie', 'XSRF-TOKEN=antani')
      .send(invalid_login)
      .expect(401)
      .end(function (err, res) {

        if (err) {
          return done(err);
        }

        validate_mandatory_headers(res.headers);

        done();
      });
  })
})

describe('POST /authentication', function () {
  it('responds 200 on valid login (valid XSRF token)', function (done) {
    app
      .post('/authentication')
      .set('X-XSRF-TOKEN', 'antani')
      .set('cookie', 'XSRF-TOKEN=antani')
      .send(valid_login)
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
