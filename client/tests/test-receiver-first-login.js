var receiver = new browser.gl.pages.receiver();

var path = require("path");

var pgp_key_path = path.resolve("../backend/globaleaks/tests/data/gpg/VALID_PGP_KEY1_PUB");

describe("Recipient1 first login", function() {
  it("should redirect to /firstlogin upon successful authentication", async function() {
    await browser.gl.utils.login_receiver("Recipient1", "globaleaks123!", "/#/login", true);
  });

  it("should be able to change password from the default one", async function() {
    await element(by.model("preferences.password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await element(by.model("preferences.check_password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await element(by.css("[data-ng-click=\"save()\"]")).click();
    await browser.gl.utils.waitForUrl("/receiver/home");
  });

  it("should be able to login with the new password", async function() {
    await browser.gl.utils.login_receiver();
  });

  it("should be able to load his/her public PGP key", async function() {
    await receiver.addPublicKey(pgp_key_path);
  });
});

describe("Recipient2 first login", function() {
  it("should redirect to /firstlogin upon successful authentication", async function() {
    await browser.gl.utils.login_receiver("Recipient2", "globaleaks123!", "/#/login", true);
  });

  it("should be able to change password from the default one", async function() {
    await element(by.model("preferences.password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await element(by.model("preferences.check_password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await element(by.css("[data-ng-click=\"save()\"]")).click();
    await browser.gl.utils.waitForUrl("/receiver/home");
  });

  it("should be able to login with the new password", async function() {
    await browser.gl.utils.login_receiver();
  });

  it("should be able to load his/her public PGP key", async function() {
    await receiver.addPublicKey(pgp_key_path);
  });
});