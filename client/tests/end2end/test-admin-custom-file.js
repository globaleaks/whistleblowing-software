var utils = require('./utils.js');

describe('Admin upload custom file', function() {
  it('should upload a file and the file should be available for download and deletion', function() {
    utils.login_admin();
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Theme customization")).click();

    var customFile = utils.makeTestFilePath('antani.js');

    browser.executeScript('angular.element(document.querySelectorAll(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    element(by.css("div.uploadfile.file-custom")).element(by.css("input")).sendKeys(customFile);

    browser.waitForAngular();

    element(by.cssContainingText("a", "Theme customization")).click();

    if (utils.testFileDownload() && utils.verifyFileDownload()) {
      element(by.css("div.uploadfile.file-custom")).element(by.cssContainingText("span", "Download"))
      .click().then(function() {
        var actualFile = utils.makeSavedFilePath('antani.js');
        utils.TestFileEquality(customFile, actualFile);
      });
    }

    element(by.id("fileList")).element(by.cssContainingText("span", "Delete")).click();
  });
});
