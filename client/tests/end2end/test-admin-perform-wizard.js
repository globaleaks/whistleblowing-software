var utils = require('./utils.js');

describe('globaLeaks setup wizard', function() {
  it('should allow the user to setup the wizard', function() {
    browser.get('/#/wizard');
    // Pick english
    element(by.model('GLTranslate.indirect.appLanguage'))
      .element(by.xpath(".//*[text()='English']")).click();

    var next1 = element(by.id('ButtonNext1'));
    utils.waitUntilReady(next1);
    // Go to step 2
    next1.click();

    // Fill out the form
    element(by.model('wizard.node.name')).sendKeys('E2E Test Instance');
    element(by.model('wizard.node.description')).sendKeys('This instance is for E2E testing');
    element(by.model('wizard.admin.mail_address')).sendKeys('globaleaks-admin@mailinator.com');
    element(by.model('admin_password')).sendKeys(utils.vars['user_password']);
    element(by.model('admin_check_password')).sendKeys(utils.vars['user_password']);

    element(by.model('wizard.receiver.name')).sendKeys('Recipient 1');
    element(by.model('wizard.receiver.mail_address')).sendKeys('globaleaks-receiver1@mailinator.com');
      
    element(by.model('wizard.context.name')).sendKeys('Context 1');
      
    // Complete the form
    element.all(by.id('ButtonNext2')).click();

    var button3 = element(by.id('ButtonNext3'));
    // Wait 20 seconds for the PGP key to generate
    utils.waitUntilClickable(button3, 30000);
    button3.click();

    expect(element(by.css('.congratulations')).isPresent()).toBe(true);

    // Go to admin interface
    element(by.id('ButtonNext4')).click();
    utils.waitForUrl('/admin/landing');
    utils.logout('/admin');
  });
});
