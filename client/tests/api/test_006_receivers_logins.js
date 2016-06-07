/*
 This set of UT validate request/responses
 against public resources.
 */

var request = require('supertest');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var utils = require('./utils.js');

var valid_login;
var invalid_login = {
  'username': 'invalid',
  'password': 'login'
};

describe('GET /public', function () {
  it('responds 200', function (done) {
    app
      .get('/public')
      .expect(200)
      .end(function (err, res) {
        if (err) {
          return done(err);
        }

        utils.validate_mandatory_headers(res.headers);

        var receiver_username = JSON.parse(JSON.stringify(res.body))['receivers'][0]['username'];

        valid_login = {
          'username': receiver_username,
          'password': 'ringobongos3cur1ty'
        };

        done();
      });
  });
});

describe('POST /authentication', function () {
  it('responds 401 on invalid login', function (done) {
    app
      .post('/authentication')
      .send(invalid_login)
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
  it('responds 200 on valid login', function (done) {
    app
      .post('/authentication')
      .send(valid_login)
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
