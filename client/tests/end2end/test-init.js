describe('init', function() {
  it('should load the app', function() {
    remote = require('selenium-webdriver/remote');
    browser.driver.setFileDetector(new remote.FileDetector());
    browser.get('/');
  });
});
