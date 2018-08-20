describe('admin configure node', function() {
  it('should configure node en internalization', function() {
    browser.setLocation('admin/content');
    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='English']")).click();
    expect(element(by.model('admin.node.header_title_homepage')).clear().sendKeys('TEXT1_EN'));
    expect(element(by.model('admin.node.presentation')).clear().sendKeys('TEXT2_EN'));

    element.all(by.cssContainingText("button", "Save")).get(0).click();
  });

  it('should configure node it internalization', function() {
    browser.setLocation('admin/content');
    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='Italiano']")).click();
    expect(element(by.model('admin.node.header_title_homepage')).clear().sendKeys('TEXT1_IT'));
    expect(element(by.model('admin.node.presentation')).clear().sendKeys('TEXT2_IT'));

    element.all(by.cssContainingText("button", "Salva")).get(0).click();

    element(by.model('GLTranslate.indirect.appLanguage')).element(by.xpath(".//*[text()='English']")).click();
  });

  it('should configure node advanced settings', function() {
    browser.setLocation('admin/advanced_settings');

    element(by.model('admin.node.enable_experimental_features')).click();
  });
});
