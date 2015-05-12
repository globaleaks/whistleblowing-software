describe('admin add receivers', function() {
  it('should add new receivers', function() {
    browser.setLocation('admin/receivers');

    var add_receiver = function(receiver) {
      element(by.model('new_receiver.name')).sendKeys(receiver);
      element(by.model('new_receiver.email')).sendKeys(receiver + '@globaleaks.org');
      return element(by.css('[data-ng-click="add_receiver()"]')).click();
    };

      
    add_receiver("Receiver1").then(function() {
      add_receiver("Receiver2").then(function() {
        add_receiver("Receiver3").then(function() {
        });
      });
    });

  });
});
