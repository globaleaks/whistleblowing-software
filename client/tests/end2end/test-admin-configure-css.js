var utils = require('./utils.js');

describe('Admin upload custom CSS', function() {
  it('should upload a file and the file should be available for download', function() {
    if (!utils.testFileUpload()) {
      return;
    }

    browser.setLocation('admin/content');

    utils.waitUntilPresent(element(by.cssContainingText("a", "Theme customization")));

    element(by.cssContainingText("a", "Theme customization")).click();

    var customCSSFile = utils.makeTestFilePath('application-home.css');

    browser.executeScript('angular.element(document.querySelectorAll(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    element(by.css("div.uploadfile.file-css")).element(by.css("input")).sendKeys(customCSSFile);

    utils.waitUntilPresent(element(by.cssContainingText("a", "Theme customization")));

    element(by.cssContainingText("a", "Theme customization")).click();

    if (utils.testFileDownload() && utils.verifyFileDownload()) {
      element(by.css("div.uploadfile.file-css")).element(by.cssContainingText("span", "Download"))
      .click().then(function() {
        var actualFile = utils.makeSavedFilePath('custom_stylesheet.css');
        utils.TestFileEquality(customCSSFile, actualFile);
      });
    }
  });
});

describe('Custom CSS classes are attached to the interface', function() {
  var EC = protractor.ExpectedConditions;

  // check that element is hidden.
  it('the logo should be hidden in the public interface', function() {
    browser.get('/');
    expect(EC.invisibilityOf($('#LogoBox')));
    expect(EC.visibilityOf($('#FooterBox')));
  });

  it('the footer should be hidden from an authenticated user', function() {
    utils.login_admin();
    browser.setLocation('/#/admin/landing');
    expect(EC.invisibilityOf($('#FooterBox')));
    expect(EC.visibilityOf($('#LogoBox')));
  });

  it('the login button should be hidden on the embedded login page', function() {
    browser.get('/#/login?embed=true');
    expect(EC.invisibilityOf($('#login-button')));
  });

  it('should allow deletion of the file', function() {
    utils.login_admin();
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Theme customization")).click();

    element(by.cssContainingText("a", "Delete")).click();

    // wait until redirect to the first tab of the admin/content section
    utils.waitUntilPresent(element(by.cssContainingText("label", "Project name")));
  });
});
