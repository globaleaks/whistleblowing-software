describe('admin add receivers', function() {
  it('should add new receivers', function() {
    browser.setLocation('admin/receivers');

    var add_receiver = function(name, address) {
      element(by.model('new_receiver.name')).sendKeys(name);
      element(by.model('new_receiver.email')).sendKeys(address);
      return element(by.css('[data-ng-click="add_receiver()"]')).click();
    };

    add_receiver("Receiver 2", "globaleaks-receiver2@mailinator.com").then(function() {
      add_receiver("Receiver 3", "globaleaks-receiver3@mailinator.com");
    });

  });
});
