var chai = require('chai'),
  should = chai.should(),
  specrequest = require('./support/request'),
  node = require('../app/scripts/spec/node'),
  submission = require('../app/scripts/spec/submission'),
  status = require('../app/scripts/spec/status');
//r_submission = require('../app/scripts/requests/submission'),
//r_status = require('../app/scripts/requests/status');

var base_path = "http://127.0.0.1:8082";

describe("GET /node", function() {
  it("should return at least one context id", function(done) {
    var node_request = specrequest(node.root(), base_path);
    node_request.end(function(result) {
      should.exist(result.res.body.contexts[0].id);
      done();
    });
  });
});

describe("Create a new submission", function() {
  it("should return submission ID", function(done) {
    var create_request = specrequest(submission.root(), base_path);
    create_request.end(function(req) {
      should.exist(req.res.body.submission_id);
      console.log(req.res.body.submission_id);
      done();
      });
  });
});

describe("Create a dummy submission", function() {
  it("should return receipt ID for the whistleblower", function(done) {
    var node_request = specrequest(node.root(), base_path);
    node_request.end(function(req) {
      var nodeinfo = req.res.body;

      var create_request = specrequest(submission.root(), base_path);
      create_request.end(function(req) {
        var submission_id = req.res.body.submission_id,
          params = {'context_selected': nodeinfo.contexts[0].id,
              'fields': {'AAA': 'BBB', 'ddd': '3213'}},
          spec = submission.status_post(submission_id, params);

          should.exist(submission_id);

          var status_request = specrequest(spec, base_path);
          status_request.end(
            function(req) {
            var spec = submission.finalize_post(submission_id, 'foobar', 'testing', 'this out');

            var finalize_request = specrequest(spec, base_path);
            finalize_request.end(
              function(req) {
                console.log("Got this response:")
                console.log(req.res.body);
                done();
            })
          });
        });
    });
  });
});



