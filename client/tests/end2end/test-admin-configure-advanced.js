var utils = require('./utils.js');

describe('adming configure advanced settings', function() {
  it('should perform main configuration', function() {
    browser.setLocation('admin/advanced_settings');
    element(by.cssContainingText("a", "Main configuration")).click();

    expect(element(by.model('admin.node.maximum_textsize')).getAttribute('value')).toEqual('4096');

    element(by.model('admin.node.maximum_textsize')).clear().sendKeys('1337');

    // enable experimental featuress that by default are disabled
    element(by.model('admin.node.enable_experimental_features')).click();

    // save settings
    element(by.css('[data-ng-click="updateNode(admin.node)"]')).click().then(function() {
      utils.emulateUserRefresh();
      expect(element(by.model('admin.node.maximum_textsize')).getAttribute('value')).toEqual('1337');
    });
  });
});

describe('adming configure advanced settings', function() {
  it('should configure HTTPS settings', function() {
    browser.setLocation('admin/advanced_settings');
    element(by.cssContainingText("a", "HTTPS settings")).click();

    expect(element(by.model('admin.node.tor2web_whistleblower')).isSelected()).toBeFalsy();

    // grant tor2web permissions
    element(by.model('admin.node.tor2web_whistleblower')).click();

    // save settings
    element(by.css('[data-ng-click="updateNode(admin.node)"]')).click().then(function() {
      utils.emulateUserRefresh();
      expect(element(by.model('admin.node.tor2web_whistleblower')).isSelected()).toBeTruthy();
    });
  });
});

describe('adming configure advanced settings - Anomaly detection thresholds', function() {
  it('should configure advanced settings', function() {
    browser.setLocation('admin/advanced_settings');
    element(by.cssContainingText("a", "Anomaly detection thresholds")).click();

    expect(element(by.model('admin.node.threshold_free_disk_percentage_high')).getAttribute('value')).toEqual('3');

    element(by.model('admin.node.threshold_free_disk_percentage_high')).clear().sendKeys('4');

    // save settings
    element(by.css('[data-ng-click="updateNode(admin.node)"]')).click().then(function() {
      utils.emulateUserRefresh();
      expect(element(by.model('admin.node.threshold_free_disk_percentage_high')).getAttribute('value')).toEqual('4');
    });
  });
});
