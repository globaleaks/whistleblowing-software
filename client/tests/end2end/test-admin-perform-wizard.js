var utils = require('./utils.js');

describe('globaLeaks setup wizard', function() {
  it('should allow the user to setup the wizard', function() {
    browser.get('/#/wizard');

    // Test language selector switching to italian and then re-switching to english
    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='Italiano']")).click();
    utils.waitUntilPresent(by.cssContainingText("form", "Benvenuto su GlobaLeaks!"));
    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='English']")).click();
    utils.waitUntilPresent(by.cssContainingText("form", "Welcome to GlobaLeaks!"));

    element.all(by.id('ButtonNext')).get(0).click();

    element(by.model('wizard.node.name')).sendKeys('E2E Test Instance');
    element(by.model('wizard.node.description')).sendKeys('This instance is for E2E testing');

    element.all(by.id('ButtonNext')).get(1).click();

    element(by.model('wizard.admin.mail_address')).sendKeys('globaleaks-admin@mailinator.com');
    element(by.model('wizard.admin.password')).sendKeys(utils.vars['user_password']);
    element(by.model('admin_check_password')).sendKeys(utils.vars['user_password']);

    element.all(by.id('ButtonNext')).get(2).click();

    element(by.model('wizard.context.name')).sendKeys('Context 1');

    element.all(by.id('ButtonNext')).get(3).click();

    element(by.model('wizard.receiver.name')).sendKeys('Recipient1');
    element(by.model('wizard.receiver.mail_address')).sendKeys('globaleaks-receiver1@mailinator.com');

    element.all(by.id('ButtonNext')).get(4).click();

    expect(element(by.css('.congratulations')).isPresent()).toBe(true);

    element.all(by.id('ButtonNext')).get(5).click();

    utils.waitForUrl('/admin/landing');

    utils.logout('/admin');
  });
});
