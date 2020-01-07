var temporary_password = "typ0drome@absurd.org";

describe("custodian first login", function() {
  it("should redirect to /firstlogin upon successful authentication", async function() {
    await browser.gl.utils.login_custodian("Custodian1", "globaleaks123!", "/#/login", true);
  });

  it("should be able to change password from the default one", async function() {
    await element(by.model("preferences.password")).sendKeys(temporary_password);
    await element(by.model("preferences.check_password")).sendKeys(temporary_password);
    await element(by.css("[data-ng-click=\"save()\"]")).click();
    await browser.gl.utils.waitForUrl("/custodian/home");
  });

  it("should be able to login with the new password", async function() {
    await browser.gl.utils.login_custodian("Custodian1", temporary_password, "/#/login", false);
  });

  it("should be able to change password accessing the user preferences", async function() {
    await element(by.cssContainingText("span", "User preferences")).click();
    await element(by.cssContainingText("a", "Password")).click();
    await element(by.model("preferences.old_password")).sendKeys(temporary_password);
    await element(by.model("preferences.password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await element(by.model("preferences.check_password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await browser.gl.utils.clickFirstDisplayed(by.css("[data-ng-click=\"save()\"]"));
  });
});
