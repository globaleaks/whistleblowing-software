/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest'),
  should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var authentication;

var population_order = 42;

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

var valid_login = function(i) {
    return {
      "username": "receiver" + i + "@antani.gov",
      "password": "receiver" + i + "@antani.gov",
      "role": "receiver"
    }
}

var invalid_login = function(i) {
  return {
    "username": "receiver" + i + "@antani.gov",
    "password": "antani",
    "role": "receiver"
  }
}

// full test on the first receiver only
for (var i=0; i<1; i++){
  describe('POST /authentication', function () {
    var credentials = valid_login(i);
    it('responds 403 on valid login [receiver'+ i + '@antani.gov:] with missing XSRF token (missing header)', function (done) {
      app
        .post('/authentication')
        .set('cookie', 'XSRF-TOKEN=antani')
        .send(credentials)
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
    var credentials = valid_login(i);
    it('responds 403 on valid login [receiver'+ i + '@antani.gov:] with missing XSRF token (missing cookie)', function (done) {
      app
        .post('/authentication')
        .set('X-XSRF-TOKEN', 'antani')
        .send(credentials)
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
    var credentials = valid_login(i);
    it('responds 403 on valid login [receiver'+ i + '@antani.gov:] with missing XSRF token (header != cookie)', function (done) {
      app
        .post('/authentication')
        .set('X-XSRF-TOKEN', 'antani')
        .set('cookie', 'XSRF-TOKEN=notantani')
        .send(credentials)
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
    var credentials = invalid_login(i);
    it('responds 401 on invalid login [receiver'+ i + '@antani.gov:] (valid XSRF token)', function (done) {
      app
        .post('/authentication')
        .set('X-XSRF-TOKEN', 'antani')
        .set('cookie', 'XSRF-TOKEN=antani')
        .send(credentials)
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
    var credentials = valid_login(i);
    it('responds 200 on valid login [receiver'+ i + '@antani.gov:] (valid XSRF token)', function (done) {
      app
        .post('/authentication')
        .set('X-XSRF-TOKEN', 'antani')
        .set('cookie', 'XSRF-TOKEN=antani')
        .send(credentials)
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
}

for (var i=1; i<population_order; i++){
  describe('POST /authentication', function () {
    var credentials = valid_login(i);
    it('responds 200 on valid login [receiver'+ i + '@antani.gov:] (valid XSRF token)', function (done) {
      app
        .post('/authentication')
        .set('X-XSRF-TOKEN', 'antani')
        .set('cookie', 'XSRF-TOKEN=antani')
        .send(credentials)
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
}