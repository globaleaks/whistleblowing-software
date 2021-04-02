describe("globaLeaks setup wizard", function() {
  it("should allow the user to setup the wizard", async function() {
    await browser.get("/#/wizard");

    await browser.gl.utils.takeScreenshot("wizard/1.png");

    await element.all(by.css(".ButtonNext")).get(0).click();

    await browser.gl.utils.takeScreenshot("wizard/2.png");

    await element(by.model("wizard.node_name")).sendKeys("GLOBALEAKS");

    await element.all(by.css(".ButtonNext")).get(1).click();

    await browser.gl.utils.takeScreenshot("wizard/3.png");

    await element(by.model("wizard.admin_username")).sendKeys("admin");
    await element(by.model("wizard.admin_name")).sendKeys("Admin");
    await element(by.model("wizard.admin_mail_address")).sendKeys("globaleaks-admin@mailinator.com");
    await element(by.model("wizard.admin_password")).sendKeys(browser.gl.utils.vars.user_password);
    await element(by.model("admin_check_password")).sendKeys(browser.gl.utils.vars.user_password);

    await element.all(by.css(".ButtonNext")).get(3).click();

    await browser.gl.utils.takeScreenshot("wizard/4.png");

    await element.all(by.model("wizard.skip_recipient_account_creation")).click();

    await element.all(by.css(".ButtonNext")).get(4).click();

    await element.all(by.css(".tos-agreement-input")).click();

    await browser.gl.utils.takeScreenshot("wizard/5.png");

    await element.all(by.css(".ButtonNext")).get(5).click();

    await browser.gl.utils.takeScreenshot("wizard/6.png");

    await element(by.cssContainingText("button", "Proceed")).click();

    await browser.gl.utils.waitForUrl("/admin/home");
  });
});
