var q = require("q");
var path = require("path");
var FirefoxProfile = require("firefox-profile");

var makeFirefoxProfile = function(preferenceMap) {
  var deferred = q.defer();
  var firefoxProfile = new FirefoxProfile();
  for (var key in preferenceMap) {
    firefoxProfile.setPreference(key, preferenceMap[key]);
  }
  firefoxProfile.encoded(function (encodedProfile) {
    var capabilities = {
      browserName: 'firefox',
      firefox_profile: encodedProfile,
      // spec path is relative to the location of config.js
      specs: ['./test-globaleaks-process.js']
    };
    deferred.resolve(capabilities);
  });
  return deferred.promise;
};

// The test directory
var tmpDir = path.resolve(__dirname, 'tmp');

exports.config = {
  // Parameters made directly available to the browser
  params: {
    tmpDir: tmpDir
  },
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
  framework: 'jasmine',
  baseUrl: 'http://127.0.0.1:8082/',
  troubleshoot: true,
  directConnect: true,
  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 60000
  }
};
