describe("admin configure, add, and delete tenants", function() {
  it("should add new tenant", async function() {
    await browser.setLocation("admin/sites");

    await element.all(by.cssContainingText("a", "Sites")).get(1).click();

    var add_tenant = async function(name) {
      await element(by.css(".show-add-tenant-btn")).click();
      await element(by.model("newTenant.name")).sendKeys(name);
      await element(by.id("add-btn")).click();
      await browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + name + "']"));
    };

    await add_tenant("Tenant 2");
    await add_tenant("Tenant 3");
  });

  it("should del existing tenants", async function() {
    await element.all((by.cssContainingText("button", "Delete"))).last().click();
    await element(by.id("modal-action-ok")).click();
  });
});
