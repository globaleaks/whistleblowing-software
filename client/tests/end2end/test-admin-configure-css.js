var utils = require('./utils.js');

describe('Admin configure custom CSS', function() {
  it('should be able to configure a custom CSS', function() {
    if (!utils.testFileUpload()) {
      return;
    }

    var EC = protractor.ExpectedConditions;

    browser.setLocation('admin/content');

    utils.waitUntilPresent(element(by.cssContainingText("a", "Theme customization")));

    element(by.cssContainingText("a", "Theme customization")).click();

    var customCSSFile = utils.makeTestFilePath('application-home.css');

    browser.executeScript('angular.element(document.querySelectorAll(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    element(by.css("div.uploadfile.file-css")).element(by.css("input")).sendKeys(customCSSFile);

    utils.waitUntilPresent(element(by.cssContainingText("label", "Project name")));

    element(by.cssContainingText("a", "Theme customization")).click();

    if (utils.testFileDownload() && utils.verifyFileDownload()) {
      element(by.css("div.uploadfile.file-css")).element(by.cssContainingText("a", "Download"))
      .click().then(function() {
        var actualFile = utils.makeSavedFilePath('custom_stylesheet.css');
        utils.TestFileEquality(customCSSFile, actualFile);
      });
    }

    browser.get('/');
    expect(EC.invisibilityOf($('#LogoBox')));
    expect(EC.visibilityOf($('#FooterBox')));

    utils.login_admin();
    browser.setLocation('/#/admin/landing');
    expect(EC.invisibilityOf($('#FooterBox')));
    expect(EC.visibilityOf($('#LogoBox')));

    browser.get('/#/login?embed=true');
    expect(EC.invisibilityOf($('#login-button')));

    utils.login_admin();
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Theme customization")).click();

    element(by.cssContainingText("a", "Delete")).click();

    // wait until redirect to the first tab of the admin/content section
    utils.waitUntilPresent(element(by.cssContainingText("label", "Project name")));
  });
});
