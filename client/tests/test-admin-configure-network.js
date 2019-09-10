describe("admin configure https", function() {
  var files = {
    priv_key: browser.gl.utils.makeTestFilePath("../../../backend/globaleaks/tests/data/https/valid/priv_key.pem"),
    cert: browser.gl.utils.makeTestFilePath("../../../backend/globaleaks/tests/data/https/valid/cert.pem"),
    chain: browser.gl.utils.makeTestFilePath("../../../backend/globaleaks/tests/data/https/valid/chain.pem"),
  };

  it("should interact with all ui elements", async function() {
    var pk_panel = element(by.css("div.card.priv-key"));
    var csr_panel = element(by.css("div.card.csr"));
    var cert_panel = element(by.css("div.card.cert"));
    var chain_panel = element(by.css("div.card.chain"));
    var modal_action = by.id("modal-action-ok");

    await browser.setLocation("admin/network");

    await element(by.cssContainingText("a", "HTTPS")).click();

    await element(by.model("admin.node.hostname")).clear();
    await element(by.model("admin.node.hostname")).sendKeys("antani.gov");
    await element(by.model("admin.node.hostname")).click();

    await element.all(by.cssContainingText("button", "Save")).get(0).click();

    await element(by.cssContainingText("button", "Proceed")).click();

    await element(by.id("HTTPSManualMode")).click();

    // Generate key
    await pk_panel.element(by.cssContainingText("button", "Generate")).click();

    // Generate csr
    await element(by.id("csrGen")).click();

    await csr_panel.element(by.model("csr_cfg.country")).sendKeys("IT");
    await csr_panel.element(by.model("csr_cfg.province")).sendKeys("Liguria");
    await csr_panel.element(by.model("csr_cfg.city")).sendKeys("Genova");
    await csr_panel.element(by.model("csr_cfg.company")).sendKeys("Internet Widgets LTD");
    await csr_panel.element(by.model("csr_cfg.department")).sendKeys("Suite reviews");
    await csr_panel.element(by.model("csr_cfg.email")).sendKeys("nocontact@certs.may.hurt");
    await element(by.id("csrSubmit")).click();

    // Download csr
    if (browser.gl.utils.testFileDownload()) {
      await csr_panel.element(by.id("downloadCsr")).click();
    }

    // Delete csr
    await element(by.id("deleteCsr")).click();
    await browser.gl.utils.waitUntilPresent(modal_action);
    await element(modal_action).click();
    await browser.wait(protractor.ExpectedConditions.stalenessOf(element(by.id("deleteCsr"))));

    // Delete key
    await element(by.id("deleteKey")).click();
    await browser.gl.utils.waitUntilPresent(modal_action);
    await element(modal_action).click();
    await browser.wait(protractor.ExpectedConditions.stalenessOf(element(by.id("deleteKey"))));

    await element(by.cssContainingText("button", "Proceed")).click();

    await element(by.id("HTTPSManualMode")).click();

    if (browser.gl.utils.testFileUpload()) {
      // Upload key
      await element(by.css("div.card.priv-key input[type=\"file\"]")).sendKeys(files.priv_key);

      // Upload cert
      await element(by.css("div.card.cert input[type=\"file\"]")).sendKeys(files.cert);

      // Upload chain
      await element(by.css("div.card.chain input[type=\"file\"]")).sendKeys(files.chain);

      // Download the cert and chain
      if (browser.gl.utils.testFileDownload()) {
        await cert_panel.element(by.id("downloadCert")).click();
        await chain_panel.element(by.id("downloadChain")).click();
      }

      // Delete chain, cert, key
      await chain_panel.element(by.id("deleteChain")).click();
      await browser.gl.utils.waitUntilPresent(modal_action);
      await element(modal_action).click();

      await cert_panel.element(by.id("deleteCert")).click();
      await browser.gl.utils.waitUntilPresent(modal_action);
      await element(modal_action).click();

      await pk_panel.element(by.id("deleteKey")).click();
      await browser.gl.utils.waitUntilPresent(modal_action);
      await element(modal_action).click();
    }
  });
});
