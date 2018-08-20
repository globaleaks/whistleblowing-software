describe('Admin configure custom CSS', function() {
  it('should be able to configure a custom CSS', function() {
    if (!browser.gl.utils.testFileUpload()) {
      return;
    }

    var EC = protractor.ExpectedConditions;

    browser.setLocation('admin/content');

    browser.gl.utils.waitUntilPresent(by.cssContainingText("a", "Theme customization"));

    element(by.cssContainingText("a", "Theme customization")).click();

    var customCSSFile = browser.gl.utils.makeTestFilePath('custom_css.css');

    browser.executeScript('angular.element(document.querySelectorAll(\'input[type="file"]\')).attr("style", "visibility: visible;");');
    element(by.css("div.uploadfile.file-css")).element(by.css("input")).sendKeys(customCSSFile);

    browser.gl.utils.waitUntilPresent(by.cssContainingText("label", "Project name"));

    element(by.cssContainingText("a", "Theme customization")).click();

    if (browser.gl.utils.testFileDownload() && browser.gl.utils.verifyFileDownload()) {
      element(by.css("div.uploadfile.file-css")).element(by.cssContainingText("a", "Download"))
      .click().then(function() {
        var actualFile = browser.gl.utils.makeSavedFilePath('custom_stylesheet.css');
        browser.gl.utils.testFileEquality(customCSSFile, actualFile);
      });
    }

    browser.get('/');
    expect(EC.invisibilityOf($('#LogoBox')));

    browser.get('/#/admin');
    expect(EC.visibilityOf($('#LogoBox')));

    browser.get('/');
    expect(EC.invisibilityOf($('#LogoBox')));

    browser.get('/#/login?embed=true');
    expect(EC.invisibilityOf($('#login-button')));

    browser.gl.utils.login_admin();
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Theme customization")).click();
    element.all(by.cssContainingText("a", "Delete")).first().click();

    // wait until redirect to the first tab of the admin/content section
    browser.gl.utils.waitUntilPresent(by.cssContainingText("label", "Project name"));
  });
});
