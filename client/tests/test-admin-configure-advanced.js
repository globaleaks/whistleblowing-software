describe("admin configure advanced settings", function() {
  it("should perform main configuration", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/settings");
    await element(by.cssContainingText("a", "Advanced")).click();

    // enable features that by default are disabled
    await element(by.model("resources.node.enable_custodian")).click();
    await element(by.model("resources.node.multisite")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).last().click();
  });
});

describe("admin disable submissions", function() {
  it("should disable submission", async function() {
    await browser.setLocation("admin/settings");
    await element(by.cssContainingText("a", "Advanced")).click();

    await element(by.model("resources.node.disable_submissions")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).last().click();

    expect(await element(by.model("resources.node.disable_submissions")).isSelected()).toBeTruthy();

    await browser.gl.utils.logout();

    await browser.get("/#/");

    expect(await browser.isElementPresent(element(by.cssContainingText("span", "Submissions disabled")))).toBe(true);

    await browser.gl.utils.login_admin();

    await browser.setLocation("admin/settings");
    await element(by.cssContainingText("a", "Advanced")).click();

    await element(by.model("resources.node.disable_submissions")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).last().click();

    expect(await element(by.model("resources.node.disable_submissions")).isSelected()).toBeFalsy();

    await browser.gl.utils.logout();

    await browser.get("/#/");

    expect(await browser.isElementPresent(element(by.cssContainingText("button", "File a report")))).toBe(true);
  });
});
