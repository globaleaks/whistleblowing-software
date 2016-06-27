var utils = require('./utils.js');

var pages = require('./pages.js');

describe('custodian first login', function() {
  var custodian = new pages.receiver();
  it('should redirect to /forcepass... upon successful authentication', function() {
    utils.login_custodian('Custodian1', utils.vars['default_password'], '/#/custodian', true);
  });

  it('should be able to change password from the default one', function() {
    var waitUrl = '/custodian/identityaccessrequests';
    custodian.changePassword(utils.vars['default_password'],
                             utils.vars['user_password'],
                             waitUrl);
  });

  it('should be able to login with the new password', function() {
    utils.login_custodian();
  });
});
