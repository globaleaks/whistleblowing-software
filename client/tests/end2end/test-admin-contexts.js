var pages = require('./pages.js');

describe('admin configure, add, and delete contexts', function() {
  var adminLog = new pages.adminLoginPage();

  beforeAll(function() {
    adminLog.login('admin', 'ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#');
    browser.setLocation('admin/contexts');
  });

  it('should configure an existing context', function() {
    var editBtn = element(by.css('.actionButtonEdit'));
    expect(editBtn.isDisplayed()).toBe(true);

    editBtn.click();
    // Add users and flip switches
    element(by.cssContainingText("span", "Recipient 2")).click();
    element(by.cssContainingText("span", "Recipient 3")).click();
    element(by.id('context-0')).element(by.css('.actionButtonAdvanced')).click();
    element(by.id('context-0')).element(by.model('context.allow_recipients_selection')).click();
    element(by.id('context-0')).element(by.model('context.enable_messages')).click();
    // Save the results
    element(by.id('context-0')).element(by.css('.actionButtonSave')).click();
    // TODO check if the result was saved

  });

  it('should add new contexts', function() {

    var add_context = function(context) {
      element(by.model('new_context.name')).sendKeys(context);
      return element(by.css('[data-ng-click="add_context()"]')).click();
    };
    add_context('Context 2');
    add_context('Context 3');
    // TODO check if the contexts were made

  });

  it('should del existing contexts', function() {
    element.all((by.css('.actionButtonDelete'))).last().click();
    // TODO delete context 2 and 3
    element(by.id('modal-action-ok')).click();
    // TODO check that the context is actually gone
  });

});
