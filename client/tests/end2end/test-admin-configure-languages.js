describe('admin configure languages', function() {
  it('should configure languages', function() {
    // Enable german and italian and then test the language selector
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Languages")).click();

    element(by.model("admin.node.languages_enabled")).evaluate("admin.node.languages_enabled = ['en', 'it', 'de'];");

    element.all(by.cssContainingText("button", "Save")).get(1).click();

    element(by.cssContainingText("a", "Languages")).click();

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
    // Set the default as german
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Languages")).click();

    element.all(by.css('.non-default-language')).get(0).click();
    element.all(by.cssContainingText("button", "Save")).get(1).click();

    // Verify that the default is set to german
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Languages")).click();
    expect(element(by.model('admin.node.default_language')).getAttribute('value')).toEqual('de');

    // Switch the default to english and disable german
    element.all(by.css('.non-default-language')).get(1).click();

    element.all(by.css('.remove-lang-btn')).get(0).click();

    element.all(by.cssContainingText("button", "Save")).get(1).click();

    // Verify that the new default is set again to english that is the first language among en/it
    browser.setLocation('admin/content');
    element(by.cssContainingText("a", "Languages")).click();
    expect(element(by.model('admin.node.default_language')).getAttribute('value')).toEqual('en');

    element.all(by.cssContainingText("button", "Save")).get(1).click();
  });
});
