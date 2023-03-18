describe("admin configure advanced settings", function() {
  it("should perform main configuration", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/settings");
    await element(by.cssContainingText("a", "Advanced")).click();

    // enable features that by default are disabled
    await element(by.model("resources.node.enable_custodian")).click();
    await element(by.model("resources.node.multisite")).click();

    if (browser.params.features.pgp) {
      await element(by.model("resources.node.pgp")).click();
    }

    await element(by.model("resources.node.viewer")).click();

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

describe("Validating custom support url", function () {
  it("Enter custom support url and browser ", async function () {
    // login as admin
    await browser.gl.utils.login_admin();

    // changed url to settings
    await browser.setLocation("admin/settings");
    await element(by.cssContainingText("a", "Advanced")).click();

    // select input field and focus and type in a new url
    await element(by.model("resources.node.custom_support_url")).clear();
    await element(by.model("resources.node.custom_support_url")).sendKeys(
      "https://www.globaleaks.org/"
    );

    // save settings
    await element.all(by.css("[data-ng-click='updateNode()']")).last().click();

    expect(
      await element(by.model("resources.node.custom_support_url")).getAttribute(
        "value"
      )
    ).toEqual("https://www.globaleaks.org/");
  });

  it("should redirect to external url on new tab", async function () {
    // change support url in settings
    await browser.setLocation("admin/settings");

    await element(by.cssContainingText("a", "Advanced")).click();

    await element(by.id("SupportLink")).click();

    const handles = await browser.getAllWindowHandles();
    await browser.switchTo().window(handles[1]);
    // setting flag for telling protractor to not wait for angular
    browser.ignoreSynchronization = true;

    const currentUrl = await browser.getCurrentUrl();
    await expect(currentUrl).toEqual("https://www.globaleaks.org/");

    // closing the new tab
    await browser.close();

    // switching back to the original tab
    await browser.switchTo().window(handles[0]);

    // Resetting flag for telling protractor to not wait for angular
    browser.ignoreSynchronization = false;
  });
});

describe("Should browser opens a pop while clicking the support icon", function () {
  it("should open a pop up model", async function () {
    // changed url to settings
    await browser.setLocation("admin/settings");
    await element(by.cssContainingText("a", "Advanced")).click();

    // clearing data in custom support url
    await element(by.model("resources.node.custom_support_url")).clear();
    // saving form
    await element.all(by.css("[data-ng-click='updateNode()']")).last().click();

    // checking the support url is empty
    expect(
      await element(by.model("resources.node.custom_support_url")).getAttribute(
        "value"
      )
    ).toEqual("");

    // clicking on support icon
    await element(by.id("SupportLink")).click();
    // checks for the pop up model by class name and show  class
    expect(await element(by.css(".modal")).isDisplayed()).toBeTruthy();

    await element(by.model("arg.text")).sendKeys("test message");
    await element(by.css(".modal #modal-action-ok")).click();

    // checking the message is present in browser
    expect(await element(by.cssContainingText("div", "Thank you. We will try to get back to you as soon as possible.")).isPresent()).toBe(true);

    await element(by.id("modal-action-cancel")).click();

    await browser.gl.utils.logout();
  });
});
 
