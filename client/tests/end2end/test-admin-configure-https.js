var utils = require('./utils.js');

describe('admin configure network settings', function() {
  it('should enable whistleblowers over https', function() {
    browser.setLocation('admin/network');

    element(by.model('admin.node.hostname')).clear().sendKeys('localhost');
    element(by.model('admin.node.onionservice')).clear().sendKeys('1234567890123456.onion');

    expect(element(by.model('admin.node.tor2web_whistleblower')).isSelected()).toBeFalsy();

    // grant tor2web permissions
    element(by.model('admin.node.tor2web_whistleblower')).click();

    // save settings
    element(by.cssContainingText("button", "Save")).click().then(function() {
      expect(element(by.model('admin.node.tor2web_whistleblower')).isSelected()).toBeTruthy();
    });
  });
});

describe('admin configure https', function() {
  var files = {
    priv_key: utils.makeTestFilePath('../../../../backend/globaleaks/tests/data/https/valid/priv_key.pem'),
    cert: utils.makeTestFilePath('../../../../backend/globaleaks/tests/data/https/valid/cert.pem'),
    chain: utils.makeTestFilePath('../../../..//backend/globaleaks/tests/data/https/valid/chain.pem'),
  };

  function enable_https() {
    var enable_btn = element(by.cssContainingText('div.launch-btns span', 'Enable'));
    enable_btn.click()

    var status_label = element(by.cssContainingText('div.status-line span span', 'Running'));
    expect(status_label.isDisplayed()).toBe(true);
  }

  function disable_https() {
    var disable_btn = element(by.cssContainingText('div.launch-btns span', 'Disable'));
    disable_btn.click()
  }

  it('should interact with all ui elements', function() {
    browser.setLocation('admin/network');
    element(by.cssContainingText("a", "HTTPS settings")).click();

    // Generate key and CSR
    var pk_panel = element(by.css('div.panel.priv-key'));

    pk_panel.element(by.cssContainingText('button', 'Generate')).click();

    var csr_panel = element(by.css('div.panel.csr'));
    var csr_gen = element(by.id('csrGen'));
    csr_gen.click()

    // Insert data into fields
    csr_panel.element(by.model('csr_cfg.commonname')).sendKeys('certs.may.hurt');
    csr_panel.element(by.model('csr_cfg.country')).sendKeys('IT');
    csr_panel.element(by.model('csr_cfg.province')).sendKeys('Liguria');
    csr_panel.element(by.model('csr_cfg.city')).sendKeys('Genova');
    csr_panel.element(by.model('csr_cfg.company')).sendKeys('Internet Widgets LTD');
    csr_panel.element(by.model('csr_cfg.department')).sendKeys('Suite reviews');
    csr_panel.element(by.model('csr_cfg.email')).sendKeys('nocontact@certs.may.hurt');

    var csr_submit = element(by.id('csrSubmit'));
    csr_submit.click();

    // Download and delete CSR
    if (utils.testFileDownload()) {
        var csr_download = csr_panel.element(by.cssContainingText('button', 'Download'));
        csr_download.click();
    }
    csr_panel.element(by.cssContainingText('button', 'Delete')).click();
    element(by.id('modal-action-ok')).click();

    // Delete key
    pk_panel.element(by.cssContainingText('button', 'Delete')).click();
    element(by.id('modal-action-ok')).click();

    // Upload key and cert
    browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.priv-key input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    pk_panel.element(by.id("keyUpload")).sendKeys(files.priv_key);

    var cert_panel = element(by.css("div.panel.cert"));
    browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.cert input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    cert_panel.element(by.css("input")).sendKeys(files.cert);

    // Enable and disable HTTPS
    enable_https();
    disable_https();

    // Upload chain
    var chain_panel = element(by.css("div.panel.chain"));
    browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.chain input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    chain_panel.element(by.css("input")).sendKeys(files.chain);


    // Download the cert and chain
    if (utils.testFileDownload()) {
      cert_panel.element(by.cssContainingText('button', 'Download'));
      chain_panel.element(by.cssContainingText('button', 'Download'));
    }

    // Enable and disable HTTPS
    enable_https();
    disable_https();

    // Delete chain, cert, key
    chain_panel.element(by.cssContainingText('button', 'Delete')).click();
    element(by.id('modal-action-ok')).click();
    cert_panel.element(by.cssContainingText('button', 'Delete')).click();
    element(by.id('modal-action-ok')).click();
    pk_panel.element(by.cssContainingText('button', 'Delete')).click();
    element(by.id('modal-action-ok')).click();
  });
});
