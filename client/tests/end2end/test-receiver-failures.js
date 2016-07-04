var pages = require('./pages.js');
var utils = require('./utils.js');

fdescribe('Resetting a user should handle', function() {

  it('the admin deleting a users credentials', function() {
    var admin = new pages.admin();
    admin.login();

    var userConf = new admin.UserConf();
    var editForm = userConf.openForm('Recipient2');

    element(by.model('user.reinitialize')).click();
    userConf.save(editForm);

    // TODO fix reset password change it should be a button next to delete.
  });

  var receiver = new pages.receiver();
  it('the user resetting their password and key', function() {
    receiver.login('Recipient2', utils.vars['default_password'], '/#/login', true);
    receiver.changePassword();
    expect(element.all(by.css('#tipListTableBody tr')).count()).toBe(0);
  });

  it('a receiver viewing a tip with data they can no longer access', function() {
    // TODO insert an error into tip messages/anwsers/files/comments then try
    // the UI
    
  });

  it('a receiver creating new comments and messages', function() {
    // TODO use this semi broken UI and send new messages, check if msgs work on 
    // refresh.
  });
});
