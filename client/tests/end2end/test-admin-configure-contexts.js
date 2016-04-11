describe('admin add contexts', function() {
  it('should add new contexts', function(done) {
    browser.setLocation('admin/contexts');

    var add_context = function(context) {
      element(by.model('new_context.name')).sendKeys(context);
      return element(by.css('[data-ng-click="add_context()"]')).click();
    };

    element(by.css('.actionButtonEdit')).click().then(function() {
      element(by.cssContainingText("span", "Recipient 2")).click();
      element(by.cssContainingText("span", "Recipient 3")).click();
      element(by.id('context-0')).element(by.css('.actionButtonAdvanced')).click().then(function() {
        element(by.id('context-0')).element(by.model('context.allow_recipients_selection')).click().then(function() {
          element(by.id('context-0')).element(by.model('context.enable_messages')).click().then(function() {
            element(by.id('context-0')).element(by.css('.actionButtonSave')).click().then(function() {
              add_context('Context 2').then(function() {
                add_context('Context 3');
                done();
              });
            });
          });
        });
      });
    });
  });
});
