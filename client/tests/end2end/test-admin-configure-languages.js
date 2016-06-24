describe('adming configure languages', function() {
  it('should configure languages', function() {
    browser.setLocation('admin/content');

    element(by.cssContainingText("a", "Languages")).click();

    element(by.id('language-enabler-it')).click();

    browser.waitForAngular();

    element(by.cssContainingText("button", "Save")).click();

    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='Italiano']")).click();

    expect(browser.isElementPresent(element(by.cssContainingText("a", "General settings")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("a", "Impostazioni generali")))).toBe(true);

    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='English']")).click();

    expect(browser.isElementPresent(element(by.cssContainingText("a", "Impostazioni generali")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("a", "General settings")))).toBe(true);
  });
});
