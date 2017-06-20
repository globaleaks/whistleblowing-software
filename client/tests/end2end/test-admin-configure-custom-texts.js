describe('admin configure custom texts', function() {
  it('should perform custom texts configuration', function() {
    browser.gl.utils.login_admin();
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Text customization")).click();

    expect(element(by.model('vars.language_to_customize')).sendKeys('English'));
    element(by.cssContainingText('option', 'Submissions disabled')).click();
    expect(element(by.model('vars.custom_text')).clear().sendKeys('Whistleblowing disabled'));

    // save settings
    element(by.id('addCustomTextButton')).click();
    browser.get('/');
    expect(browser.isElementPresent(element(by.cssContainingText("button", "Submissions disabled")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("button", "Whistleblowing disabled")))).toBe(true);

    browser.gl.utils.login_admin();

    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Text customization")).click();

    // save settings
    element(by.css('.deleteCustomTextButton')).click();
    browser.get('/');
    expect(browser.isElementPresent(element(by.cssContainingText("button", "Whistleblowing disabled")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("button", "Submissions disabled")))).toBe(true);

    browser.gl.utils.login_admin();
  });
});
