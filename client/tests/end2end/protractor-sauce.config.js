var fs = require('fs');
var specs = JSON.parse(fs.readFileSync('tests/end2end/specs.json'));

var browser_capabilities = JSON.parse(process.env.SELENIUM_BROWSER_CAPABILITIES);
browser_capabilities['name'] = 'GlobaLeaks-E2E';
browser_capabilities['tunnel-identifier'] = process.env.TRAVIS_JOB_NUMBER;
browser_capabilities['build'] = process.env.TRAVIS_BUILD_NUMBER;

exports.config = {
  framework: 'jasmine',

  baseUrl: 'http://localhost:9000/',

  troubleshoot: false,
  directConnect: false,

  sauceUser: process.env.SAUCE_USERNAME,
  sauceKey: process.env.SAUCE_ACCESS_KEY,
  capabilities: browser_capabilities,

  params: {
    'testFileDownload': false,
    'verifyFileDownload': false,
    'tmpDir': '/tmp/globaleaks-download',
  },

  specs: specs,

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 360000
  }
};
