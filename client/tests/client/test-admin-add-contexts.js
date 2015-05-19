describe('admin add contexts', function() {
  it('should add new contexts', function() {
    browser.setLocation('admin/contexts');

    var add_context = function(context) {
      element(by.model('new_context.name')).sendKeys(context);
      return element(by.css('[data-ng-click="add_context()"]')).click();
    };

    add_context("Context 2").then(function() {
      add_context("Context 3");
    });

  });
});
