describe('adming configure languages', function() {
  it('should configure languages', function() {
    // Enable german and italian and then test the language selector
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Languages")).click();
    element(by.id('language-enabler-de')).click();
    element(by.id('language-enabler-it')).click();
    element(by.cssContainingText("button", "Save")).click();

    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='Deutsch']")).click();

    expect(browser.isElementPresent(element(by.cssContainingText("a", "General settings")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("a", "Allgemeine Einstellungen")))).toBe(true);

    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='Italiano']")).click();

    expect(browser.isElementPresent(element(by.cssContainingText("a", "Allgemeine Einstellungen")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("a", "Impostazioni generali")))).toBe(true);

    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='English']")).click();

    expect(browser.isElementPresent(element(by.cssContainingText("a", "Impostazioni generali")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("a", "General settings")))).toBe(true);
  });

  it('should configure default language', function() {
    // Disable italian and set the default as german
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Languages")).click();
    element(by.model('admin.node.default_language')).element(by.xpath(".//*[text()='German']")).click();
    element(by.cssContainingText("button", "Save")).click();


    // Verify that the default is set to german and then disable it.
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Languages")).click();
    expect(element(by.model('admin.node.default_language')).getAttribute('value')).toEqual('string:de');
    element(by.id('language-enabler-de')).click();
    element(by.cssContainingText("button", "Save")).click();

    // Verify that the new default is set again to english that is the first language among en/it
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Languages")).click();
    expect(element(by.model('admin.node.default_language')).getAttribute('value')).toEqual('string:en');
    element(by.cssContainingText("button", "Save")).click();
  });
});
