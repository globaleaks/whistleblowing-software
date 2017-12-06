var fs = require('fs');
var specs = JSON.parse(fs.readFileSync('tests/end2end/specs.json'));

var tmp = [];
for (var i=0; i<specs.length; i++) {
  tmp.push('tests/end2end/' + specs[i]);
}

specs = tmp;

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

  allScriptsTimeout: 180000,

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 180000
  },

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
