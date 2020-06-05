describe("admin configure node", function() {
  it("should configure node en internalization", async function() {
    await browser.setLocation("admin/content");
    element(by.model("GLTranslate.state.language")).element(by.xpath(".//*[text()='English']")).click();
    await element(by.model("resources.node.header_title_homepage")).clear();
    await element(by.model("resources.node.header_title_homepage")).sendKeys("TEXT1_EN");
    await element(by.model("resources.node.presentation")).clear();
    await element(by.model("resources.node.presentation")).sendKeys("TEXT2_EN");

    await element.all(by.cssContainingText("button", "Save")).get(0).click();
  });

  it("should configure node it internalization", async function() {
    await browser.setLocation("admin/content");
    element(by.model("GLTranslate.state.language")).element(by.xpath(".//*[text()='Italiano']")).click();
    await element(by.model("resources.node.header_title_homepage")).clear();
    await element(by.model("resources.node.header_title_homepage")).sendKeys("TEXT1_IT");
    await element(by.model("resources.node.presentation")).clear();
    await element(by.model("resources.node.presentation")).sendKeys("TEXT2_IT");

    await element.all(by.cssContainingText("button", "Salva")).get(0).click();

    element(by.model("GLTranslate.state.language")).element(by.xpath(".//*[text()='English']")).click();
  });
});
