var utils = require('./utils.js');

describe('admin login', function() {
  it('should login as admin', function() {
    browser.sleep(3000);
    utils.login_admin();
  });
});
