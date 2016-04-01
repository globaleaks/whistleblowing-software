var q = require("q");
var FirefoxProfile = require("firefox-profile");

var makeFirefoxProfile = function(preferenceMap) {
  var deferred = q.defer();
  var firefoxProfile = new FirefoxProfile();
  for (var key in preferenceMap) {
    if (preferenceMap.hasOwnProperty(key)) {
      firefoxProfile.setPreference(key, preferenceMap[key]);
    }
  }
  firefoxProfile.encoded(function (encodedProfile) {
    var capabilities = {
      browserName: 'firefox',
      firefox_profile: encodedProfile,
    };
    deferred.resolve(capabilities);
  });
  return deferred.promise;
};

// The test directory for downloaded files
var tmpDir = '/tmp/';

exports.config = {
  framework: 'jasmine',

  baseUrl: 'http://127.0.0.1:8082/',

  troubleshoot: true,
  directConnect: true,

  params: {
    'testFileDownload': true,
    'tmpDir': tmpDir
  },

  specs: [
    'tests/end2end/test-init.js',
    'tests/end2end/test-admin-perform-wizard.js',
    'tests/end2end/test-admin-login.js',
    'tests/end2end/test-admin-configure-node.js',
    'tests/end2end/test-admin-configure-users.js',
    'tests/end2end/test-admin-configure-contexts.js',
    'tests/end2end/test-receiver-first-login.js',
    'tests/end2end/test-globaleaks-process.js'
  ],

  getMultiCapabilities: function() {
    return q.all([ 
      makeFirefoxProfile({
        "browser.download.folderList": 2,
        // One of these does the job
        "browser.download.dir": tmpDir,
        "browser.download.defaultFolder": tmpDir,
        "browser.download.downloadDir": tmpDir,
        "browser.helperApps.neverAsk.saveToDisk": "application/octet-stream"
      })
    ]);
  },

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 180000
  }
};
