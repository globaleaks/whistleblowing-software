describe('admin add receivers', function() {
  it('should add new receivers', function() {
    browser.setLocation('admin/receivers');

    var add_receiver = function(username, name, address) {
      element(by.model('new_receiver.username')).sendKeys(username);
      element(by.model('new_receiver.name')).sendKeys(name);
      element(by.model('new_receiver.email')).sendKeys(address);
      return element(by.css('[data-ng-click="add_receiver()"]')).click();
    };

    add_receiver("receiver2", "Recipient 2", "globaleaks-receiver2@mailinator.com").then(function() {
      add_receiver("receiver3", "Recipient 3", "globaleaks-receiver3@mailinator.com");
    });
  });
});
