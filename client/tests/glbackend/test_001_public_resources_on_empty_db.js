/*
  This set of UT validate request/responses
  against public resources.
*/

var request = require('supertest'),
    should = require('should');

var host = 'http://127.0.0.1:8082';

var app = request(host);

public_resources = [
  {
    'url': '/',
    'type': 'text/html',
    'status': 200
  },
  {
    'url': '/index.html',
    'type': 'text/html',
    'status': 200
  },
  {
    'url': '/styles.css',
    'type': 'text/css',
    'status': 200
  },
  {
    'url': '/scripts.js',
    'type': 'application/javascript',
    'status': 200
  },
  {
    'url': '/static/custom_stylesheet.css',
    'type': 'text/css',
    'status': 200
  },
  {
    'url': '/static/globaleaks_logo.png',
    'type': 'image/png',
    'status': 200
  },
  {
    'url': '/fonts/glyphicons-halflings-regular.woff',
    'type': 'text/html; charset=UTF-8',
    'status': 200
  },
  {
    'url': '/node',
    'type': 'application/json',
    'status': 200
  },
  {
    'url': '/contexts',
    'type': 'application/json',
    'status': 200
  },
  {
    'url': '/receivers',
    'type': 'application/json',
    'status': 200
  },
  {
    'url': '/unexistent',
    'type': 'text/html; charset=UTF-8',
    'status': 404
  }
];

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

public_resources.forEach(function(req){
  describe('GET ' + req['url'], function(){
    it('responds with ' + req['type'], function(done){
      app
      .get(req['url'])
      .expect('Content-Type', req['type'])
      .expect(req['status'])
      .end(function(err, res) {
        if (err) {
          return done(err);
        } else {

          validate_mandatory_headers(res.headers);

          if (req['type'] == 'application/json') {
            // TODO JSON FORMAT VALIDATION
            // https://npmjs.org/package/jsonschema
            done();
          } else {
           done();
          }
        } 
      });
    })
  })
})

public_resources.forEach(function(req){
  describe('POST ' + req['url'], function(){
    it('responds with 403', function(done){
      app
      .post(req['url'])
      .expect(403)
      .end(function(err, res) {
        if (err) {
          return done(err);
        } else {

          validate_mandatory_headers(res.headers);

          if (req['type'] == 'application/json') {
            // TODO JSON FORMAT VALIDATION
            // https://npmjs.org/package/jsonschema
            done();
          } else {
           done();
          }
        }
      });
    })
  })
})

public_resources.forEach(function(req){
  describe('DELETE ' + req['url'], function(){
    it('responds with ' + req['type'], function(done){
      app
      .del(req['url'])
      .expect(403)
      .end(function(err, res) {
        if (err) {
          return done(err);
        } else {

          validate_mandatory_headers(res.headers);

          if (req['type'] == 'application/json') {
            // TODO JSON FORMAT VALIDATION
            // https://npmjs.org/package/jsonschema
            done();
          } else {
           done();
          }
        }
      });
    })
  })
})
