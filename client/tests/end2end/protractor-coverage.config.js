var fs = require('fs');
var specs = JSON.parse(fs.readFileSync('tests/end2end/specs.json'));

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
var tmpDir = '/tmp/globaleaks-downloads';

exports.config = {
  framework: 'jasmine',

  baseUrl: 'http://127.0.0.1:8082/',

  troubleshoot: false,
  directConnect: true,

  params: {
    'testFileDownload': true,
    'verifyFileDownload': true,
    'tmpDir': tmpDir
  },

  specs: specs,

  getMultiCapabilities: function() {
    return makeFirefoxProfile({
      "intl.accept_language": "en_US",
      "browser.download.folderList": 2,
      // One of these does the job
      "browser.download.dir": tmpDir,
      "browser.download.defaultFolder": tmpDir,
      "browser.download.downloadDir": tmpDir,
      "browser.helperApps.neverAsk.saveToDisk": "application/octet-stream",
    });
  },

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 180000
  },

  plugins : [{
    path: '../../node_modules/protractor-istanbul-plugin'
  }]
};
