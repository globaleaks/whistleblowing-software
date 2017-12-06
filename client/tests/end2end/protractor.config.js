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
      args: ['--window-size=1280,1024'],
      prefs: {
        'download': {
          'prompt_for_download': false,
          'default_directory': tmpDir
        }
      }
    }
  },

  allScriptsTimeout: 60000,

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 60000
  },

  plugins: [
    {
      package: 'protractor-console-plugin',
      failOnWarning: false,
      failOnError: true,
      logWarnings: true,
      exclude: []
    }
  ],

  onPrepare: function() {
    browser.gl = {
      'utils': require('./utils.js'),
      'pages': require('./pages.js')
    }

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
