/*
 This set of UT validate request/responses
 against authenticated admion resources on empty db.
 */

var request = require('supertest');

var host = 'http://127.0.0.1:8082';

var app = request(host);

var utils = require('./utils.js');

describe('POST /wizard', function () {
  var wizard = {
    node: {
      name: 'name',
      description: 'description',
      allow_unencrypted: true
    },
    admin: {
      mail_address: 'giovanni.pellerano@evilaliv3.org',
      password: utils.password
    },
    context: utils.get_context(),
    receiver: utils.get_user()
  }

  it('responds 201 on valid completed wizard', function (done) {
    app
      .post('/wizard')
      .send(wizard)
      .expect(201)
      .end(function (err, res) {
        if (err) {
          return done(err);
        }

        utils.validate_mandatory_headers(res.headers);

        done();
      });
  });
});
