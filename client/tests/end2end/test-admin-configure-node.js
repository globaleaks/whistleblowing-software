describe('adming configure node', function() {
  it('should configure node', function() {
    browser.setLocation('admin/advanced_settings');

    // simplify the configuration in order to simplfy initial tests
    element(by.model('admin.node.disable_security_awareness_badge')).click();

    // enable all receivers to postpone and delete tips
    element(by.model('admin.node.can_postpone_expiration')).click();
    element(by.model('admin.node.can_delete_submission')).click();

    element(by.css('[data-ng-click="updateNode(admin.node)"]')).click();
  });
});
