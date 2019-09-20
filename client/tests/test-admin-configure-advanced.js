describe("admin configure advanced settings", function() {
  it("should perform main configuration", async function() {
    await browser.setLocation("admin/advanced_settings");
    await element(by.cssContainingText("a", "Main configuration")).click();

    // enable experimental features that by default are disabled
    await element(by.model("admin.node.enable_experimental_features")).click();
    await element(by.model("admin.node.enable_custodian")).click();

    await element(by.css("body").sendKeys(protractor.Key.F1);

    await element(by.model("admin.node.encryption")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).first().click();
  });
});

describe("admin after enabling encryption", function() {
  it("should redirect to password change upon successful authentication", async function() {
    await browser.gl.utils.login_admin("admin", browser.gl.utils.vars["user_password"], "/#/login", true);
  });

  it("should be able to change password from the default one", async function() {
    await element(by.model("preferences.password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await element(by.model("preferences.check_password")).sendKeys(browser.gl.utils.vars["user_password"]);
    await element(by.css("[data-ng-click=\"save()\"]")).click();
    await browser.gl.utils.waitForUrl("/admin/home");
  });
});

describe("admin configure advanced settings", function() {
  it("should configure url redirects", async function() {
    await browser.setLocation("admin/advanced_settings");
    await element(by.cssContainingText("a", "URL redirects")).click();

    for (var i = 0; i < 3; i++) {
      await element(by.model("new_redirect.path1")).sendKeys("yyyyyyyy-" + i.toString());
      await element(by.model("new_redirect.path2")).sendKeys("xxxxxxxx");
      await element(by.cssContainingText("button", "Add")).click();
      await element.all(by.cssContainingText("button", "Delete")).first().click();
    }
  });

  it("should configure advanced settings", async function() {
    await browser.setLocation("admin/advanced_settings");
    await element(by.cssContainingText("a", "Anomaly detection thresholds")).click();

    expect(await element(by.model("admin.node.threshold_free_disk_percentage_high")).getAttribute("value")).toEqual("3");

    await element(by.model("admin.node.threshold_free_disk_percentage_high")).clear();
    await element(by.model("admin.node.threshold_free_disk_percentage_high")).sendKeys("4");

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).get(1).click();

    expect(await element(by.model("admin.node.threshold_free_disk_percentage_high")).getAttribute("value")).toEqual("4");
  });
});

describe("admin disable submissions", function() {
  it("should disable submission", async function() {
    await browser.setLocation("admin/advanced_settings");
    await element(by.cssContainingText("a", "Main configuration")).click();

    await element(by.model("admin.node.disable_submissions")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).first().click();

    expect(await element(by.model("admin.node.disable_submissions")).isSelected()).toBeTruthy();

    await browser.get("/#/");

    expect(await browser.isElementPresent(element(by.cssContainingText("span", "Submissions disabled")))).toBe(true);

    await browser.gl.utils.login_admin();

    await browser.setLocation("admin/advanced_settings");

    await element(by.model("admin.node.disable_submissions")).click();

    // save settings
    await element.all(by.css("[data-ng-click=\"updateNode()\"]")).first().click();

    expect(await element(by.model("admin.node.disable_submissions")).isSelected()).toBeFalsy();

    await browser.get("/#/");

    expect(await browser.isElementPresent(element(by.cssContainingText("button", "Blow the whistle")))).toBe(true);

    await browser.gl.utils.login_admin();
  });
});
