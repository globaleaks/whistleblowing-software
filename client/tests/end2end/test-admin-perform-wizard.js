describe('globaLeaks setup wizard', function() {
  it('should allow the user to setup the wizard', function() {
    browser.get('/#/wizard');

    // Test language selector switching to italian and then re-switching to english
    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='Italiano']")).click();
    browser.gl.utils.waitUntilPresent(by.cssContainingText("form", "Benvenuto su GlobaLeaks!"));
    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='English']")).click();
    browser.gl.utils.waitUntilPresent(by.cssContainingText("form", "Welcome to GlobaLeaks!"));

    element.all(by.id('ButtonNext')).get(0).click();

    element(by.model('wizard.node.name')).sendKeys('E2E Test Instance');
    element(by.model('wizard.node.description')).sendKeys('This instance is for E2E testing');

    element.all(by.id('ButtonNext')).get(1).click();

    element(by.id('profile-0')).click();

    element.all(by.id('ButtonNext')).get(2).click();

    element(by.model('wizard.admin.mail_address')).sendKeys('globaleaks-admin@mailinator.com');
    element(by.model('wizard.admin.password')).sendKeys(browser.gl.utils.vars['user_password']);
    element(by.model('admin_check_password')).sendKeys(browser.gl.utils.vars['user_password']);

    element.all(by.id('ButtonNext')).get(3).click();

    element(by.model('wizard.receiver.name')).sendKeys('Recipient1');
    element(by.model('wizard.receiver.mail_address')).sendKeys('globaleaks-receiver1@mailinator.com');

    element.all(by.id('ButtonNext')).get(4).click();

    element.all(by.css('.tos-agreement')).click();

    element.all(by.id('ButtonNext')).get(5).click();

    expect(element(by.css('.congratulations')).isPresent()).toBe(true);

    element.all(by.id('ButtonNext')).get(6).click();

    browser.gl.utils.waitForUrl('/admin/home');
  });
});
