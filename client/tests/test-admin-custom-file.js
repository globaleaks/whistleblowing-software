describe("Admin upload custom file", function() {
  it("should upload a file and the file should be available for download and deletion", function() {
    if (!browser.gl.utils.testFileUpload()) {
      return;
    }

    browser.setLocation("admin/content");

    browser.gl.utils.waitUntilPresent(by.cssContainingText("a", "Files"));

    element(by.cssContainingText("a", "Files")).click();

    var customFile = browser.gl.utils.makeTestFilePath("nyancat.pdf");

    browser.executeScript("angular.element(document.querySelectorAll('input[type=\"file\"]')).attr(\"style\", \"visibility: visible\")");
    element(by.css("span.file-custom")).element(by.css("input")).sendKeys(customFile);

    browser.gl.utils.waitUntilPresent(by.cssContainingText("label", "Project name"));

    element(by.cssContainingText("a", "Files")).click();

    element(by.id("fileList")).element(by.cssContainingText("span", "Delete")).click();
  });
});
