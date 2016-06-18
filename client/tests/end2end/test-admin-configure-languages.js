var utils = require('./utils.js');

describe('adming configure languages', function() {
  it('should configure languages', function() {
    browser.setLocation('admin/content');

    element(by.cssContainingText("a", "Languages")).click();

    element(by.id('language-enabler-it')).click();

    browser.waitForAngular();

    element(by.cssContainingText("button", "Save")).click();

    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='Italiano']")).click();

    utils.waitUntilReady(element(by.cssContainingText("a", "Impostazioni generali")));
    expect(browser.isElementPresent(element(by.cssContainingText("a", "General settings")))).toBe(false);

    element(by.model('GLTranslate.indirect.appLanguage')).sendKeys('en');

    utils.waitUntilReady(element(by.cssContainingText("a", "General settings")));
    expect(browser.isElementPresent(element(by.cssContainingText("a", "Impostazioni generali")))).toBe(false);
  });
});
