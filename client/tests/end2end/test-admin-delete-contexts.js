describe('admin del contexts', function() {
  it('should del existing contexts', function(done) {
    browser.setLocation('admin/contexts');

    element.all((by.css('.actionButtonDelete'))).last().click().then(function() {
      element(by.id('modal-action-ok')).click().then(function() {
        done();
      });
    });
  });
});
