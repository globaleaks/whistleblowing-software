describe("Admin configure custom CSS", function() {
  it("should be able to configure a custom CSS", async function() {
    var customCSSFile = browser.gl.utils.makeTestFilePath("style.css");

    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/content");

    await browser.gl.utils.waitUntilPresent(by.cssContainingText("a", "Theme customization"));

    await element(by.cssContainingText("a", "Theme customization")).click();

    await element(by.css("div.uploadfile.file-css input")).sendKeys(customCSSFile);

    await browser.gl.utils.waitUntilPresent(by.cssContainingText("label", "Project name"));

    await browser.gl.utils.logout();
  });
});
