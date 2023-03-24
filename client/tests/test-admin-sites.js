describe("admin configure, add, and delete tenants", function() {
  it("should add new tenant", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/sites");

    await element.all(by.cssContainingText("a", "Sites")).get(1).click();

    var add_tenant = async function(name) {
      await element(by.css(".show-add-tenant-btn")).click();
      await element(by.model("newTenant.name")).sendKeys(name);
      await element(by.id("add-btn")).click();
      await browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + name + "']"));
    };

    await element.all(by.cssContainingText("a", "Sites")).first().click();

    await add_tenant("Platform A");
    await add_tenant("Platform B");
    await add_tenant("Platform C");

    await browser.gl.utils.takeScreenshot("admin/sites_management_sites.png");
  });

  it("should del existing tenants", async function() {
    await element.all((by.cssContainingText("button", "Delete"))).last().click();
    await element(by.id("modal-action-ok")).click();
  });

  it("should configure sites options", async function() {
    await element(by.cssContainingText("a", "Options")).click();
    await browser.gl.utils.takeScreenshot("admin/sites_management_options.png");
    await browser.gl.utils.logout();
  });
});
