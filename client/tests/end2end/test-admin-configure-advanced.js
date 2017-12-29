describe('admin configure advanced settings', function() {
  it('should perform main configuration', function() {
    browser.setLocation('admin/advanced_settings');
    element(by.cssContainingText("a", "Main configuration")).click();

    // enable experimental features that by default are disabled
    element(by.model('admin.node.enable_experimental_features')).click();

    // enable multitenancy feauture
    element(by.model('admin.node.enable_multisite')).click();

    // save settings
    element.all(by.css('[data-ng-click="updateNode(admin.node)"]'));
  });

  it('should configure short urls', function() {
    browser.setLocation('admin/advanced_settings');
    element(by.cssContainingText("a", "URL shortener")).click();

    for (var i = 0; i < 3; i++) {
      element(by.model('new_shorturl.shorturl')).sendKeys('shorturl-' + i.toString());
      element(by.model('new_shorturl.longurl')).sendKeys('longurl');
      element(by.cssContainingText("button", "Add")).click();
      element(by.cssContainingText("button", "Delete")).click();
    }
  });

  it('should configure advanced settings', function() {
    browser.setLocation('admin/advanced_settings');
    element(by.cssContainingText("a", "Anomaly detection thresholds")).click();

    expect(element(by.model('admin.node.threshold_free_disk_percentage_high')).getAttribute('value')).toEqual('3');

    element(by.model('admin.node.threshold_free_disk_percentage_high')).clear().sendKeys('4');

    // save settings
    element.all(by.css('[data-ng-click="updateNode(admin.node)"]')).last().click().then(function() {
      expect(element(by.model('admin.node.threshold_free_disk_percentage_high')).getAttribute('value')).toEqual('4');
    });
  });
});

describe('admin disable submissions', function() {
  it('should disable submission', function() {
    browser.setLocation('admin/advanced_settings');
    element(by.cssContainingText("a", "Main configuration")).click();

    element(by.model('admin.node.disable_submissions')).click();

    // save settings
    element.all(by.css('[data-ng-click="updateNode(admin.node)"]')).first().click().then(function() {
      expect(element(by.model('admin.node.disable_submissions')).isSelected()).toBeTruthy();
    });

    browser.get('/#/');

    expect(browser.isElementPresent(element(by.cssContainingText("span", "Submissions disabled")))).toBe(true);

    browser.gl.utils.login_admin();

    browser.setLocation('admin/advanced_settings');

    element(by.model('admin.node.disable_submissions')).click();

    // save settings
    element.all(by.css('[data-ng-click="updateNode(admin.node)"]')).first().click().then(function() {
      expect(element(by.model('admin.node.disable_submissions')).isSelected()).toBeFalsy();
    });

    browser.get('/#/');

    expect(browser.isElementPresent(element(by.cssContainingText("button", "Blow the whistle")))).toBe(true);

    browser.gl.utils.login_admin();
  });
});
