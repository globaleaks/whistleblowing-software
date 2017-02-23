describe('admin configure network settings', function() {
  it('should enable whistleblowers over https', function() {
    browser.setLocation('admin/network');

    element(by.model('admin.node.public_site')).clear().sendKeys('https://127.0.0.1');

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
  files = {
    priv_key: '',
    cert: '',
    chain: '',
  };

  it('should interact with all ui elements', function() {
    browser.setLocation('admin/network');
    element(by.cssContainingText("a", "HTTPS Settings")).click();

    // Generate key and CSR
    element(by.css('div.panel.priv-key')).element(by.cssContainingText('span', 'Generate')).click();
    element(by.css('div.panel.csr')).element(by.cssContainingText('span', 'Generate')).click();

    // Download and delete CSR
    element(by.css('div.panel.csr')).element(by.cssContainingText('span', 'Download')).click();
    element(by.css('div.panel.csr')).element(by.cssContainingText('span', 'Delete')).click();

    // Delete key
    element(by.css('div.panel.priv_key')).element(by.cssContainingText('span', 'Delete')).click();

    // Upload key and cert
    browser.executeScript('angular.element(document.querySelectorAll(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    element(by.css("div.panel.priv_key")).element(by.css("input")).sendKeys(files.priv_key);

    browser.executeScript('angular.element(document.querySelectorAll(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    element(by.css("div.panel.cert")).element(by.css("input")).sendKeys(files.priv_key);

    // Enable HTTPS

    // Disable HTTPS

    // Upload chain

    // Enable and disable HTTPS

    // Delete chain, cert

    // Fin

  });
});
