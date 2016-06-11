var utils = require('./utils.js');

describe('adming configure custom texts', function() {
  it('should perform custom texts configuration', function() {
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Texts customization")).click();

    expect(element(by.model('vars.language_to_customize')).sendKeys('English'));
    element(by.cssContainingText('option', 'Whistleblowing disabled')).click();
    expect(element(by.model('vars.custom_text')).clear().sendKeys('Submissions disabled'));

    // save settings
    element(by.id('addCustomTextButton')).click().then(function() {
      browser.get('/');
      expect(browser.isElementPresent(element(by.cssContainingText("button", "Whistleblowing disabled")))).toBe(false);
      expect(browser.isElementPresent(element(by.cssContainingText("button", "Submissions disabled")))).toBe(true);
    });

    utils.login_admin();

    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Texts customization")).click();

    // save settings
    element(by.css('.deleteCustomTextButton')).click().then(function() {
      browser.get('/');
      expect(browser.isElementPresent(element(by.cssContainingText("button", "Submissions disabled")))).toBe(false);
      expect(browser.isElementPresent(element(by.cssContainingText("button", "Whistleblowing disabled")))).toBe(true);
    });
  });
});
