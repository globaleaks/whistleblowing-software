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
    utils.waitUntilPresent(by.cssContainingText('div.launch-btns span', 'Enable'));
    element(by.cssContainingText('div.launch-btns span', 'Enable')).click();

    utils.waitUntilPresent(by.cssContainingText('div.status-line span span', 'Running'));
  }

  function disable_https() {
    utils.waitUntilPresent(by.cssContainingText('div.launch-btns span', 'Disable'));
    element(by.cssContainingText('div.launch-btns span', 'Disable')).click();
  }

  it('should interact with all ui elements', function() {
    browser.setLocation('admin/network');
    element(by.cssContainingText("a", "HTTPS settings")).click();

    var pk_panel = element(by.css('div.panel.priv-key'));
    var csr_panel = element(by.css('div.panel.csr'));
    var cert_panel = element(by.css('div.panel.cert'));
    var chain_panel = element(by.css('div.panel.chain'));
    var modal_action = by.id('modal-action-ok');

    // Generate key
    pk_panel.element(by.cssContainingText('button', 'Generate')).click();

    // Generate csr
    element(by.id('csrGen')).click();
    csr_panel.element(by.model('csr_cfg.commonname')).sendKeys('certs.may.hurt');
    csr_panel.element(by.model('csr_cfg.country')).sendKeys('IT');
    csr_panel.element(by.model('csr_cfg.province')).sendKeys('Liguria');
    csr_panel.element(by.model('csr_cfg.city')).sendKeys('Genova');
    csr_panel.element(by.model('csr_cfg.company')).sendKeys('Internet Widgets LTD');
    csr_panel.element(by.model('csr_cfg.department')).sendKeys('Suite reviews');
    csr_panel.element(by.model('csr_cfg.email')).sendKeys('nocontact@certs.may.hurt');
    element(by.id('csrSubmit')).click();

    // Download csr
    if (utils.testFileDownload()) {
      csr_panel.element(by.id('downloadCsr')).click();
    }

    // Delete csr
    element(by.id('deleteCsr')).click();
    element(modal_action).click();
    browser.wait(protractor.ExpectedConditions.stalenessOf(element(by.id('deleteCsr'))));

    // Delete key
    element(by.id('deleteKey')).click();
    element(modal_action).click();
    browser.wait(protractor.ExpectedConditions.stalenessOf(element(by.id('deleteKey'))));

    if (utils.testFileUpload()) {
      // Upload key
      browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.priv-key input[type="file"]\')).attr("style", "visibility: visible")');
      element(by.css("div.panel.priv-key input")).sendKeys(files.priv_key);

      // Upload cert
      browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.cert input[type="file"]\')).attr("style", "visibility: visible")');
      element(by.css("div.panel.cert input")).sendKeys(files.cert);

      // Upload chain
      browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.chain input[type="file"]\')).attr("style", "visibility: visible")');
      element(by.css("div.panel.chain input")).sendKeys(files.chain);

      // Download the cert and chain
      if (utils.testFileDownload()) {
        cert_panel.element(by.id('downloadCert')).click();
        chain_panel.element(by.id('downloadChain')).click();
      }

      // Enable and disable HTTPS
      enable_https();
      disable_https();

      // Delete chain, cert, key
      chain_panel.element(by.id('deleteChain')).click();
      modal_action = by.id('modal-action-ok');
      utils.waitUntilPresent(modal_action);
      element(modal_action).click();

      cert_panel.element(by.id('deleteCert')).click();
      modal_action = by.id('modal-action-ok');
      utils.waitUntilPresent(modal_action);
      element(modal_action).click();

      pk_panel.element(by.id('deleteKey')).click();
      modal_action = by.id('modal-action-ok');
      utils.waitUntilPresent(modal_action);
      element(modal_action).click();
    }
  });
});
