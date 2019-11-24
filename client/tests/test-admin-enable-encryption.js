describe("admin configure advanced settings", function() {
  it("should perform main configuration", async function() {
    await browser.setLocation("admin/advanced_settings");
    await element(by.cssContainingText("a", "Main configuration")).click();

    await element(by.css("body")).sendKeys(protractor.Key.F1);

    await element(by.model("resources.node.encryption")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).first().click();
  });

  it("should redirect to password change upon successful authentication", async function() {
    await browser.gl.utils.login_admin("admin", "w1z4rdp4ssw0rd!", "/#/login", true);
  });

  it("should be able to change password from the default one", async function() {
    await element(by.model("preferences.password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await element(by.model("preferences.check_password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await element(by.css("[data-ng-click=\"save()\"]")).click();
    await browser.gl.utils.waitForUrl("/admin/home");
  });
});
