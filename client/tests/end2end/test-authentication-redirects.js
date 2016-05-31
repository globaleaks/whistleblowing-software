var utils = require('./utils.js');

describe('perform rediects on authenticated pages', function() {
  //beforeEach(function() {
    //browser.refresh();
  //});

  it('test rtip redirect to login page', function() {
    browser.get('/#/status/2f0535eb-9710-47e5-8082-5f882d4ec770');

    utils.waitForUrl('/login');
  });

  it('test wbtip redirect to the homepage', function() {
    browser.get('/#/status');

    utils.waitForUrl('/');
  });

  it('test admin redirect to login page', function() {
    browser.get('/#/admin/advanced_settings');

    utils.waitForUrl('/admin');
  });

  it('test custodian redirect to login page', function() {
    browser.get('/#/custodian/identityaccessrequests');

    utils.waitForUrl('/custodian');
  });
});

