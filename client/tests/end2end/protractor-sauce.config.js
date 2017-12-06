var fs = require('fs');
var specs = JSON.parse(fs.readFileSync('tests/end2end/specs.json'));

var browser_capabilities = JSON.parse(process.env.SELENIUM_BROWSER_CAPABILITIES);
browser_capabilities['name'] = 'GlobaLeaks-E2E';
browser_capabilities['tunnel-identifier'] = process.env.TRAVIS_JOB_NUMBER;
browser_capabilities['build'] = process.env.TRAVIS_BUILD_NUMBER;
browser_capabilities['tags'] = [process.env.TRAVIS_BRANCH];

exports.config = {
  framework: 'jasmine',

  baseUrl: 'http://localhost:9000/',

  troubleshoot: false,
  directConnect: false,

  sauceUser: process.env.SAUCE_USERNAME,
  sauceKey: process.env.SAUCE_ACCESS_KEY,
  sauceBuild: process.env.TRAVIS_BUILD_NUMBER,
  capabilities: browser_capabilities,

  params: {
    'testFileDownload': false,
    'verifyFileDownload': false,
    'tmpDir': '/tmp/globaleaks-download',
  },

  specs: specs,

  allScriptsTimeout: 360000,

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 360000
  },

  onPrepare: function() {
    browser.gl = {
      'utils': require('./utils.js'),
      'pages': require('./pages.js')
    },

    browser.addMockModule('GLServices', function () {
      angular.module('GLServices').factory('Test', function () {
        return true;
      });
    });

    browser.addMockModule('disableTooltips', function() {
      angular.module('disableTooltips', []).config(['$uibTooltipProvider', function($uibTooltipProvider) {
        $uibTooltipProvider.options({appendToBody: true, trigger: 'none', enable: false});
        $uibTooltipProvider.options = function() {};
      }]);
    });
  }
};
