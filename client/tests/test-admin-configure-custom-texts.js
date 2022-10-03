describe("admin configure custom texts", function() {
  it("should perform custom texts configuration", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/content");
    await element(by.cssContainingText("a", "Text customization")).click();

    await element(by.cssContainingText("option", "Submissions disabled")).click();
    await element(by.model("vars.custom_text")).clear();
    await element(by.model("vars.custom_text")).sendKeys("Whistleblowing disabled");

    // save settings
    await element(by.id("addCustomTextButton")).click();

    await browser.gl.utils.logout();

    await browser.get("/");
    expect(await browser.isElementPresent(element(by.cssContainingText("button", "Submissions disabled")))).toBe(false);
    expect(await browser.isElementPresent(element(by.cssContainingText("button", "Whistleblowing disabled")))).toBe(true);

    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/content");
    await element(by.cssContainingText("a", "Text customization")).click();

    // save settings
    await element(by.css(".deleteCustomTextButton")).click();

    await browser.gl.utils.logout();

    await browser.get("/");
    expect(await browser.isElementPresent(element(by.cssContainingText("button", "Whistleblowing disabled")))).toBe(false);
    expect(await browser.isElementPresent(element(by.cssContainingText("button", "Submissions disabled")))).toBe(true);
  });
});
