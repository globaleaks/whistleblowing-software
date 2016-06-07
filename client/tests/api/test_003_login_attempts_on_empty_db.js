/*
 This set of UT validate login attempt
 to for the admin user.
 */

var request = require('supertest');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var utils = require('./utils.js');

describe('POST /authentication', function () {
  it('responds 401 on invalid admin login', function (done) {
    app
      .post('/authentication')
      .send(utils.invalid_admin_login)
      .expect(401)
      .end(function (err, res) {

        if (err) {
          return done(err);
        }

        utils.validate_mandatory_headers(res.headers);

        done();
      });
  });
});

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

        done();
      });
  });
});
