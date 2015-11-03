describe('admin add contexts', function() {
  it('should add new contexts', function() {
    var deferred = protractor.promise.defer();

    browser.setLocation('admin/contexts');

    var add_context = function(context) {
      element(by.model('new_context.name')).sendKeys(context);
      return element(by.css('[data-ng-click="add_context()"]')).click();
    };

    element(by.id('context-0')).click().then(function() {
      element(by.id('context-0')).element(by.css('.actionButtonAdvancedSettings')).click().then(function() {
        element(by.id('context-0')).element(by.model('context.show_receivers')).click().then(function() {
          element(by.id('context-0')).element(by.css('.actionButtonContextSave')).click().then(function() {
            add_context('Context 2').then(function() {
              add_context('Context 3');
              deferred.fulfill();
            });
          });
        });
      });
    });

    return deferred;
  });
});
