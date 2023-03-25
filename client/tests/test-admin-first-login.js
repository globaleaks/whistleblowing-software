describe("admin login", function() {
  it("should login as admin", async function() {
    await browser.gl.utils.login_admin();

    await element(by.id("PreferencesLink")).click();
    await browser.gl.utils.waitForUrl("/admin/preferences");
    await element(by.cssContainingText("button", "Account recovery key")).click();
    await element(by.model("secret")).sendKeys(browser.gl.utils.vars.user_password);
    await element(by.cssContainingText("button", "Confirm")).click();
    await element(by.cssContainingText("button", "Close")).click();

    await browser.gl.utils.logout();
  });
});
