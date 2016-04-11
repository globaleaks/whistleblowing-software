var pages = require('./pages.js');

describe('admin del users', function() {
  var adminLog = new pages.adminLoginPage();

  it('should del existing users', function() {
    adminLog.login('admin', 'ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#');
    browser.setLocation('admin/users');

    element.all((by.css('.actionButtonDelete'))).last().click();
    element(by.id('modal-action-ok')).click();
  });
});
