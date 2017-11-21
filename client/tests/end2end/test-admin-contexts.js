describe('admin configure, add, and delete contexts', function() {
  it('should configure an existing context', function() {
    browser.setLocation('admin/contexts');

    var ctx = element(by.id('context-0'));
    ctx.element(by.cssContainingText("button", "Edit")).click();

    // Add users and flip switches
    ctx.element(by.className('add-receiver-btn')).click();

    var input = element(by.id('ReceiverContextAdder')).all(by.css('input')).last();
    input.sendKeys('Recipient2' + protractor.Key.ENTER);

    ctx.element(by.className('add-receiver-btn')).click();
    input = element(by.id('ReceiverContextAdder')).all(by.css('input')).last();
    input.sendKeys('Recipient3' + protractor.Key.ENTER);

    ctx.element(by.cssContainingText("button", "Advanced settings")).click();

    ctx.element(by.model('context.allow_recipients_selection')).click();

    browser.gl.utils.waitUntilPresent(by.model('context.select_all_receivers'));

    ctx.element(by.model('context.select_all_receivers')).click();

    ctx.element(by.model('context.enable_messages')).click();
    ctx.element(by.model('context.enable_rc_to_wb_files')).click();

    // Save the results
    ctx.element(by.cssContainingText("button", "Save")).click();

    // TODO check if the result was saved
  });

  it('should add new contexts', function() {
    var add_context = function(context_name) {
      element(by.css('.show-add-context-btn')).click();
      element(by.model('new_context.name')).sendKeys(context_name);
      element(by.id('add-btn')).click();
      browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + context_name + "']"));
    };

    add_context('Context 2');
    add_context('Context 3');
    // TODO check if the contexts were made
  });

  it('should del existing contexts', function() {
    element.all((by.cssContainingText("button", "Delete"))).last().click();
    // TODO delete context 2 and 3
    element(by.id('modal-action-ok')).click();
    // TODO check that the context is actually gone
  });
});
