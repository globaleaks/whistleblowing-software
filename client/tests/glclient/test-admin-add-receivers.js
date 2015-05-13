describe('admin add receivers', function() {
  it('should add new receivers', function() {
    browser.setLocation('admin/receivers');

    element(by.model('new_receiver.name')).sendKeys("Glenn Greenwald");
    element(by.model('new_receiver.email')).sendKeys('glenn.greenwal@mailinator.com');
    element(by.css('[data-ng-click="add_receiver()"]')).click();

  });
});
