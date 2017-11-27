describe('admin configure https', function() {
  var files = {
    priv_key: browser.gl.utils.makeTestFilePath('../../../../backend/globaleaks/tests/data/https/valid/priv_key.pem'),
    cert: browser.gl.utils.makeTestFilePath('../../../../backend/globaleaks/tests/data/https/valid/cert.pem'),
    chain: browser.gl.utils.makeTestFilePath('../../../..//backend/globaleaks/tests/data/https/valid/chain.pem'),
  };

  it('should interact with all ui elements', function() {
    var pk_panel = element(by.css('div.panel.priv-key'));
    var csr_panel = element(by.css('div.panel.csr'));
    var cert_panel = element(by.css('div.panel.cert'));
    var chain_panel = element(by.css('div.panel.chain'));
    var modal_action = by.id('modal-action-ok');

    browser.setLocation('admin/network');

    element(by.cssContainingText("a", "HTTPS")).click();

    element(by.model('admin.node.hostname')).clear();
    element(by.model('admin.node.hostname')).sendKeys('antani.gov');
    element(by.model('admin.node.hostname')).click();

    element.all(by.cssContainingText("button", "Save")).get(1).click();

    element(by.cssContainingText("button", "Proceed")).click();

    element(by.id("HTTPSAutoMode")).click()

    element(by.cssContainingText("button", "Cancel")).click();
    browser.gl.utils.waitUntilPresent(modal_action);
    element(modal_action).click();

    element(by.cssContainingText("button", "Proceed")).click();

    element(by.id("HTTPSManualMode")).click()

    // Generate key
    pk_panel.element(by.cssContainingText('button', 'Generate')).click();

    // Generate csr
    element(by.id('csrGen')).click();

    csr_panel.element(by.model('csr_cfg.country')).sendKeys('IT');
    csr_panel.element(by.model('csr_cfg.province')).sendKeys('Liguria');
    csr_panel.element(by.model('csr_cfg.city')).sendKeys('Genova');
    csr_panel.element(by.model('csr_cfg.company')).sendKeys('Internet Widgets LTD');
    csr_panel.element(by.model('csr_cfg.department')).sendKeys('Suite reviews');
    csr_panel.element(by.model('csr_cfg.email')).sendKeys('nocontact@certs.may.hurt');
    element(by.id('csrSubmit')).click();

    // Download csr
    if (browser.gl.utils.testFileDownload()) {
      csr_panel.element(by.id('downloadCsr')).click();
    }

    // Delete csr
    element(by.id('deleteCsr')).click();
    browser.gl.utils.waitUntilPresent(modal_action);
    element(modal_action).click();
    browser.wait(protractor.ExpectedConditions.stalenessOf(element(by.id('deleteCsr'))));

    // Delete key
    element(by.id('deleteKey')).click();
    browser.gl.utils.waitUntilPresent(modal_action);
    element(modal_action).click();
    browser.wait(protractor.ExpectedConditions.stalenessOf(element(by.id('deleteKey'))));

    element(by.cssContainingText("button", "Proceed")).click();

    element(by.id("HTTPSManualMode")).click()

    if (browser.gl.utils.testFileUpload()) {
      // Upload key
      browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.priv-key input[type="file"]\')).attr("style", "display: block; visibility: visible")');
      element(by.css("div.panel.priv-key input[type=\"file\"]")).sendKeys(files.priv_key);

      // Upload cert
      browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.cert input[type="file"]\')).attr("style", "display: block; visibility: visible")');
      element(by.css("div.panel.cert input[type=\"file\"]")).sendKeys(files.cert);

      // Upload chain
      browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.chain input[type="file"]\')).attr("style", "display: block; visibility: visible")');
      element(by.css("div.panel.chain input[type=\"file\"]")).sendKeys(files.chain);

      // Download the cert and chain
      if (browser.gl.utils.testFileDownload()) {
        cert_panel.element(by.id('downloadCert')).click();
        chain_panel.element(by.id('downloadChain')).click();
      }

      // Delete chain, cert, key
      chain_panel.element(by.id('deleteChain')).click();
      element(modal_action).click();

      cert_panel.element(by.id('deleteCert')).click();
      browser.gl.utils.waitUntilPresent(modal_action);
      element(modal_action).click();

      pk_panel.element(by.id('deleteKey')).click();
      browser.gl.utils.waitUntilPresent(modal_action);
      element(modal_action).click();
    }
  });
});
