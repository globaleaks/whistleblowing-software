describe("admin configure advanced settings", function() {
  it("should perform main configuration", async function() {
    await browser.setLocation("admin/advanced");
    await element(by.cssContainingText("a", "Main configuration")).click();

    // enable features that by default are disabled
    await element(by.model("resources.node.enable_custodian")).click();
    await element(by.model("resources.node.multisite")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).first().click();
  });

  it("should configure advanced settings", async function() {
    await browser.setLocation("admin/advanced");
    await element(by.cssContainingText("a", "Anomaly detection thresholds")).click();

    expect(await element(by.model("resources.node.threshold_free_disk_percentage_high")).getAttribute("value")).toEqual("3");

    await element(by.model("resources.node.threshold_free_disk_percentage_high")).clear();
    await element(by.model("resources.node.threshold_free_disk_percentage_high")).sendKeys("4");

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).get(1).click();

    expect(await element(by.model("resources.node.threshold_free_disk_percentage_high")).getAttribute("value")).toEqual("4");
  });
});

describe("admin disable submissions", function() {
  it("should disable submission", async function() {
    await browser.setLocation("admin/advanced");
    await element(by.cssContainingText("a", "Main configuration")).click();

    await element(by.model("resources.node.disable_submissions")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).first().click();

    expect(await element(by.model("resources.node.disable_submissions")).isSelected()).toBeTruthy();

    await browser.get("/#/");

    expect(await browser.isElementPresent(element(by.cssContainingText("span", "Submissions disabled")))).toBe(true);

    await browser.gl.utils.login_admin();

    await browser.setLocation("admin/advanced");

    await element(by.model("resources.node.disable_submissions")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).first().click();

    expect(await element(by.model("resources.node.disable_submissions")).isSelected()).toBeFalsy();

    await browser.get("/#/");

    expect(await browser.isElementPresent(element(by.cssContainingText("button", "Blow the whistle")))).toBe(true);
  });
});
