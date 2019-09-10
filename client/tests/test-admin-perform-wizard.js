describe("globaLeaks setup wizard", function() {
  it("should allow the user to setup the wizard", async function() {
    await browser.get("/#/wizard");

    await element.all(by.css(".ButtonNext")).get(0).click();

    await element(by.model("wizard.node_name")).sendKeys("E2E Test Instance");

    await element.all(by.css(".ButtonNext")).get(1).click();

    //await element(by.id('profile-0')).click();

    //await element.all(by.css('.ButtonNext')).get(2).click();

    await element(by.model("wizard.admin_name")).sendKeys("Admin");
    await element(by.model("wizard.admin_mail_address")).sendKeys("globaleaks-admin@mailinator.com");
    await element(by.model("wizard.admin_password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await element(by.model("admin_check_password")).sendKeys(browser.gl.utils.vars["user_password"]);

    await element.all(by.css(".ButtonNext")).get(3).click();

    await element(by.model("wizard.receiver_name")).sendKeys("Recipient1");
    await element(by.model("wizard.receiver_mail_address")).sendKeys("globaleaks-receiver1@mailinator.com");

    await element.all(by.css(".ButtonNext")).get(4).click();

    await element.all(by.css(".tos-agreement-input")).click();

    await element.all(by.css(".ButtonNext")).get(5).click();

    expect(await element(by.css(".congratulations")).isPresent()).toBe(true);

    await browser.gl.utils.waitUntilPresent(by.cssContainingText("button", "Administration interface"));

    await element(by.cssContainingText("button", "Administration interface")).click();

    await browser.gl.utils.waitForUrl("/admin/home");
  });
});
