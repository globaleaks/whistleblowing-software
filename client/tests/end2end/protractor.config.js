var fs = require('fs');
var specs = JSON.parse(fs.readFileSync('tests/end2end/specs.json'));

// The test directory for downloaded files
var tmpDir = '/tmp/globaleaks-download';

exports.config = {
  framework: 'jasmine',

  onPrepare: function() {
    var failFast = require('jasmine-fail-fast');
    jasmine.getEnv().addReporter(failFast.init());
  },

  baseUrl: 'http://127.0.0.1:8082/',

  troubleshoot: true,
  directConnect: true,

  params: {
    'testFileDownload': true,
    'verifyFileDownload': false,
    'tmpDir': tmpDir
  },

  specs: specs,

  capabilities: {
    'browserName': 'chrome',
    'chromeOptions': {
      prefs: {
        'download': {
          'prompt_for_download': false,
          'default_directory': tmpDir
        }
      }
    }
  },

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 60000,
  }
};
