var fs = require('fs');
var specs = JSON.parse(fs.readFileSync('tests/end2end/specs.json'));

// The test directory for downloaded files
var tmpDir = '/tmp/globaleaks-downloads';

exports.config = {
  framework: 'jasmine',

  baseUrl: 'http://127.0.0.1:8082/',

  troubleshoot: false,
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
    defaultTimeoutInterval: 60000
  },

  plugins: [
    {
      package: 'protractor-accessibility-plugin',
      chromeA11YDevTools: {
        treatWarningsAsFailures: false
      }
    },
    {
      package: 'protractor-console-plugin',
      failOnWarning: false,
      failOnError: true,
      logWarnings: true,
      exclude: []
    }
  ]
};
