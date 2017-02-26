var path = require('path');

describe('admin configure network settings', function() {
  it('should enable whistleblowers over https', function() {
    browser.setLocation('admin/network');

    element(by.model('admin.node.hostname')).clear().sendKeys('localhost');

    expect(element(by.model('admin.node.tor2web_whistleblower')).isSelected()).toBeFalsy();

    // grant tor2web permissions
    element(by.model('admin.node.tor2web_whistleblower')).click();

    // save settings
    element(by.cssContainingText("button", "Save")).click().then(function() {
      expect(element(by.model('admin.node.tor2web_whistleblower')).isSelected()).toBeTruthy();
    });
  });
});

fdescribe('admin configure https', function() {
  var files = {
    priv_key: path.resolve('../backend/globaleaks/tests/data/https/privkey.pem'),
    cert: path.resolve('../backend/globaleaks/tests/data/https/cert.pem'),
    chain: path.resolve('../backend/globaleaks/tests/data/https/chain.pem'),
  };

  function enable_https() {
    var enable_btn = element(by.cssContainingText('div.launch-btns span', 'Enable'));
    enable_btn.click()

    var status_label = element(by.cssContainingText('div.status-line span', 'Running'));
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
    browser.actions().mouseMove(csr_gen);
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
    browser.actions().mouseMove(csr_submit);
    csr_submit.click();

    // Download and delete CSR
    var csr_download = csr_panel.element(by.cssContainingText('button', 'Download'));
    browser.actions().mouseMove(csr_download);
    csr_download.click();
    csr_panel.element(by.cssContainingText('button', 'Delete')).click();
    element(by.id('modal-action-ok')).click();

    // Delete key
    pk_panel.element(by.cssContainingText('button', 'Delete')).click();
    element(by.id('modal-action-ok')).click();

    // Upload key and cert
    browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.priv-key input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    pk_panel.element(by.id("keyUpload")).sendKeys(files.priv_key);

    var pk_upload = pk_panel.element(by.id('keyUploadBtn'));
    pk_upload.click();


    var cert_panel = element(by.css("div.panel.cert"));
    browser.executeScript('angular.element(document.querySelectorAll(\'div.panel.cert input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    cert_panel.element(by.css("input")).sendKeys(files.cert);
    //browser.sleep(7500);

    var cert_upload = cert_panel.element(by.cssContainingText('span.file-upload label span', 'Upload'));
    cert_upload.click();
    //browser.sleep(7500);

    // Enable and disable HTTPS
    enable_https();
    disable_https();

    // Upload chain
    var chain_panel = element(by.css("div.panel.chain"))
    var chain_upload = chain_panel.element(by.cssContainingText('span.file-upload label span', 'Upload'));
    chain_upload.click();
    //browser.sleep(7500);

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
