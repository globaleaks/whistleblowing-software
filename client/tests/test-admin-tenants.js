describe('admin configure, add, and delete tenants', function() {
  it('should add new tenant', function() {
    browser.setLocation('admin/tenants');

    var add_tenant = function(tenant_label) {
      element(by.css('.show-add-tenant-btn')).click();
      element(by.model('newTenant.label')).sendKeys(tenant_label);
      element(by.id('add-btn')).click();
      browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + tenant_label + "']"));
    };

    add_tenant('Tenant 2');
    add_tenant('Tenant 3');
  });

  it('should del existing tenants', function() {
    element.all((by.cssContainingText("button", "Delete"))).last().click();
    element(by.id('modal-action-ok')).click();

    // TODO check that the tenant is actually gone
  });
});
