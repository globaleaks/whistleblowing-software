describe('admin del users', function() {
  it('should del existing users', function(done) {
    browser.setLocation('admin/users');

    element.all((by.css('.actionButtonDelete'))).last().click().then(function() {
      element(by.id('modal-action-ok')).click().then(function() {
        done();
      });
    });
  });
});
