var utils = require('./utils.js');

describe('init', function() {
  it('should load the app', function() {
    var remote = require('selenium-webdriver/remote');
    browser.driver.setFileDetector(new remote.FileDetector());

    if (!utils.isMobile()) {
      browser.driver.manage().window().maximize();
    }

    browser.get('/');
  });
});
