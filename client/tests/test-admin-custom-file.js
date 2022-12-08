describe("Admin upload custom file", function() {
  it("should upload a file and the file should be available for download and deletion", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/settings");

    await element(by.cssContainingText("a", "Theme customization")).click();

    var customFile = browser.gl.utils.makeTestFilePath("antani.pdf");

    await element(by.css("div.file-custom")).element(by.css("input")).sendKeys(customFile);

    await browser.wait(function() {
      return element(by.cssContainingText("label", "Project name")).isDisplayed().then(function(present) {
        return present;
      });
    });

    await element(by.cssContainingText("a", "Theme customization")).click();

    await element(by.id("fileList")).element(by.cssContainingText("span", "Delete")).click();

    await browser.gl.utils.logout();
  });
});
