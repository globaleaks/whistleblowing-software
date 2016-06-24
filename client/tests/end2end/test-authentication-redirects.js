var utils = require('./utils.js');

describe('perform rediects on authenticated pages', function() {
  it('test rtip redirect to login page', function() {
    browser.get('/#/status/2f0535eb-9710-47e5-8082-5f882d4ec770');

    utils.waitForUrl('/login?src=%2Fstatus%2F2f0535eb-9710-47e5-8082-5f882d4ec770');
  });

  it('test wbtip redirect to the homepage', function() {
    browser.get('/#/status');

    utils.waitForUrl('/?src=%2Fstatus');
  });

  it('test admin redirect to login page', function() {
    browser.get('/#/admin/advanced_settings');

    utils.waitForUrl('/admin?src=%2Fadmin%2Fadvanced_settings');
  });

  it('test custodian redirect to login page', function() {
    browser.get('/#/custodian/identityaccessrequests');

    utils.waitForUrl('/custodian?src=%2Fcustodian%2Fidentityaccessrequests');
  });
});

// TODO
describe('Click on the GL as a role,', function() {

  it('No auth should redirect home', function() {
    browser.get('/#/login');

    $('#LogoBox a').click();

    utils.waitForUrl('/#/'); 
  });


  it('Receiver after clicking on a tip should be brought home', function() {
    // login_receiver

  });

});

