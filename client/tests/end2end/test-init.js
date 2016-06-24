describe('init', function() {
  it('should load the app', function() {
    var remote = require('selenium-webdriver/remote');
    browser.driver.setFileDetector(new remote.FileDetector());

    browser.driver.manage().window().maximize();

    browser.get('/');
  });
});
