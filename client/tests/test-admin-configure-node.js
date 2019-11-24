describe("admin configure node", function() {
  it("should configure node en internalization", async function() {
    await browser.setLocation("admin/content");
    await element.all(by.cssContainingText("a", "English")).get(0).click();
    await element(by.model("resources.node.header_title_homepage")).clear();
    await element(by.model("resources.node.header_title_homepage")).sendKeys("TEXT1_EN");
    await element(by.model("resources.node.presentation")).clear();
    await element(by.model("resources.node.presentation")).sendKeys("TEXT2_EN");

    await element.all(by.cssContainingText("button", "Save")).get(0).click();
  });

  it("should configure node it internalization", async function() {
    await browser.setLocation("admin/content");
    await element.all(by.cssContainingText("a", "Italiano")).get(0).click();
    await element(by.model("resources.node.header_title_homepage")).clear();
    await element(by.model("resources.node.header_title_homepage")).sendKeys("TEXT1_IT");
    await element(by.model("resources.node.presentation")).clear();
    await element(by.model("resources.node.presentation")).sendKeys("TEXT2_IT");

    await element.all(by.cssContainingText("button", "Salva")).get(0).click();

    await element.all(by.cssContainingText("a", "English")).get(0).click();
  });

  it("should configure node advanced settings", async function() {
    await browser.setLocation("admin/advanced_settings");

    await element(by.model("resources.node.enable_experimental_features")).click();
  });
});
