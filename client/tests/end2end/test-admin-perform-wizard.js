describe('globaLeaks setup wizard', function() {
  it('should allow the user to setup the wizard', function() {
    browser.get('/#/wizard');

    element.all(by.css('.ButtonNext')).get(0).click();

    element(by.model('wizard.node_name')).sendKeys('E2E Test Instance');

    element.all(by.css('.ButtonNext')).get(1).click();

    //element(by.id('profile-0')).click();

    //element.all(by.css('.ButtonNext')).get(2).click();

    element(by.model('wizard.admin_name')).sendKeys('Admin');
    element(by.model('wizard.admin_mail_address')).sendKeys('globaleaks-admin@mailinator.com');
    element(by.model('wizard.admin_password')).sendKeys(browser.gl.utils.vars['user_password']);
    element(by.model('admin_check_password')).sendKeys(browser.gl.utils.vars['user_password']);

    element.all(by.css('.ButtonNext')).get(3).click();

    element(by.model('wizard.receiver_name')).sendKeys('Recipient1');
    element(by.model('wizard.receiver_mail_address')).sendKeys('globaleaks-receiver1@mailinator.com');

    element.all(by.css('.ButtonNext')).get(4).click();

    element.all(by.css('.tos-agreement')).click();

    element.all(by.css('.ButtonNext')).get(5).click();

    expect(element(by.css('.congratulations')).isPresent()).toBe(true);

    element.all(by.css('.ButtonNext')).get(6).click();

    browser.gl.utils.waitForUrl('/admin/home');
  });
});
