describe('admin configure, add, and delete contexts', function() {
  it('should configure an existing context', function() {
    browser.setLocation('admin/contexts');

    element(by.id('context-0')).element(by.css('.actionButtonEdit')).click();
    // Add users and flip switches
    element(by.cssContainingText("span", "Recipient2")).click();
    element(by.cssContainingText("span", "Recipient3")).click();
    element(by.id('context-0')).element(by.css('.actionButtonAdvanced')).click();
    element(by.id('context-0')).element(by.model('context.allow_recipients_selection')).click();

    browser.gl.utils.waitUntilPresent(by.model('context.select_all_receivers'));

    element(by.id('context-0')).element(by.model('context.select_all_receivers')).click();

    element(by.id('context-0')).element(by.model('context.enable_messages')).click();
    element(by.id('context-0')).element(by.model('context.enable_rc_to_wb_files')).click();
    // Save the results
    element(by.id('context-0')).element(by.css('.actionButtonSave')).click();
    // TODO check if the result was saved
  });

  it('should add new contexts', function() {
    var add_context = function(context_name) {
      element(by.model('new_context.name')).sendKeys(context_name);
      element(by.id('add-button')).click();
      browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + context_name + "']"));
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
