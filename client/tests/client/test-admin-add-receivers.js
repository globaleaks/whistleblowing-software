describe('admin add receivers', function() {
  it('should add new receivers', function() {
    var deferred = protractor.promise.defer();

    browser.setLocation('admin/receivers');

    var add_receiver = function(username, name, address) {
      element(by.model('new_receiver.username')).sendKeys(username);
      element(by.model('new_receiver.name')).sendKeys(name);
      element(by.model('new_receiver.email')).sendKeys(address);
      return element(by.css('[data-ng-click="add_receiver()"]')).click();
    };

    add_receiver("receiver2", "Receiver 2", "globaleaks-receiver2@mailinator.com").then(function() {
      add_receiver("receiver3", "Receiver 3", "globaleaks-receiver3@mailinator.com");
      deferred.fulfill();
    });

    return deferred;
  });
});
