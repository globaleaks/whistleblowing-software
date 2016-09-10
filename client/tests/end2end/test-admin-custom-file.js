var utils = require('./utils.js');

describe('Admin upload custom file', function() {
  it('should upload a file and the file should be available for download and deletion', function() {
    if (!utils.testFileUpload()) {
      return;
    }

    browser.setLocation('admin/content');

    utils.waitUntilPresent(element(by.cssContainingText("a", "Theme customization")));

    element(by.cssContainingText("a", "Theme customization")).click();

    var customFile = utils.makeTestFilePath('nyancat.pdf');

    browser.executeScript('angular.element(document.querySelectorAll(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    element(by.css("div.uploadfile.file-custom")).element(by.css("input")).sendKeys(customFile);

    utils.waitUntilPresent(element(by.cssContainingText("a", "Theme customization")));

    element(by.cssContainingText("a", "Theme customization")).click();

    element(by.id("fileList")).element(by.cssContainingText("span", "Delete")).click();
  });
});
