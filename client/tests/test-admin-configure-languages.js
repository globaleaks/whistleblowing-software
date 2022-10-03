describe("admin configure languages", function() {
  it("should configure languages", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/content");
    await element(by.cssContainingText("a", "Languages")).click();

    await element(by.className("add-language-btn")).click();

    await element(by.model("resources.node.languages_enabled")).evaluate("resources.node.languages_enabled = ['en', 'it', 'de'];");

    await element.all(by.cssContainingText("button", "Save")).get(1).click();

    await element(by.cssContainingText("a", "Languages")).click();

    await element(by.model("GLTranslate.state.language")).element(by.xpath(".//*[text()='Deutsch']")).click();

    expect(await browser.isElementPresent(element(by.cssContainingText("a", "Site settings")))).toBe(false);
    expect(await browser.isElementPresent(element(by.cssContainingText("a", "Seiteneinstellungen")))).toBe(true);

    await element(by.model("GLTranslate.state.language")).element(by.xpath(".//*[text()='Italiano']")).click();

    expect(await browser.isElementPresent(element(by.cssContainingText("a", "Seiteneinstellungen")))).toBe(false);
    expect(await browser.isElementPresent(element(by.cssContainingText("a", "Impostazioni sito")))).toBe(true);

    await element(by.model("GLTranslate.state.language")).element(by.xpath(".//*[text()='English']")).click();

    expect(await browser.isElementPresent(element(by.cssContainingText("a", "Impostazioni sito")))).toBe(false);
    expect(await browser.isElementPresent(element(by.cssContainingText("a", "Site settings")))).toBe(true);
  });

  it("should configure default language", async function() {
    // Set the default as german
    await browser.setLocation("admin/content");
    await element(by.cssContainingText("a", "Languages")).click();

    await element.all(by.css(".non-default-language")).get(0).click();
    await element.all(by.cssContainingText("button", "Save")).get(1).click();

    // Verify that the default is set to german
    await browser.setLocation("admin/content");
    await element(by.cssContainingText("a", "Languages")).click();

    // Switch the default to english and disable german
    await element.all(by.css(".non-default-language")).get(0).click();

    await element.all(by.css(".remove-lang-btn")).get(0).click();

    await element.all(by.cssContainingText("button", "Save")).get(1).click();

    // Verify that the new default is set again to english that is the first language among en/it
    await browser.setLocation("admin/content");
    await element(by.cssContainingText("a", "Languages")).click();

    await element.all(by.cssContainingText("button", "Save")).get(1).click();
  });

  it("should configure italian texts", async function() {
    await browser.setLocation("admin/content");

    // Switch to Italian
    await element(by.model("GLTranslate.state.language")).element(by.xpath(".//*[text()='Italiano']")).click();
    await element(by.model("resources.node.header_title_homepage")).clear();
    await element(by.model("resources.node.header_title_homepage")).sendKeys("TEXT1_IT");
    await element(by.model("resources.node.presentation")).clear();
    await element(by.model("resources.node.presentation")).sendKeys("TEXT2_IT");
    await element.all(by.cssContainingText("button", "Salva")).get(0).click();

    // Switch back to English
    await element(by.model("GLTranslate.state.language")).element(by.xpath(".//*[text()='English']")).click();

    await browser.gl.utils.logout();
  });
});
