describe('admin configure, add, and delete tenants', function() {
  it('should add new tenant', function() {
    browser.setLocation('admin/tenants');

    var add_tenant = function(tenant_label) {
      element(by.model('new_tenant.label')).sendKeys(tenant_label);
      element(by.id('add-button')).click();
      browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + tenant_label + "']"));
    };

    add_tenant('Tenant 2');
    add_tenant('Tenant 3');
  });

  it('should del existing tenants', function() {
    element.all((by.css('.actionButtonDelete'))).last().click();
    element(by.id('modal-action-ok')).click();

    // TODO check that the tenant is actually gone
  });
});
