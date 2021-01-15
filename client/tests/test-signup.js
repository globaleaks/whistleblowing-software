describe("admin enable signup", function() {
  it("should enable signup", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/sites");
    await element(by.cssContainingText("a", "Options")).click();
    await element(by.model("resources.node.enable_signup")).click();
    await element.all(by.cssContainingText("button", "Save")).last().click();
  });
});

describe("user perform signup", function() {
  it("should perform signup", async function() {
    await browser.get("/#/");
    await element(by.model("signup.subdomain")).sendKeys("test");
    await element(by.model("signup.name")).sendKeys("Name");
    await element(by.model("signup.surname")).sendKeys("Surname");
    await element(by.model("signup.email")).sendKeys("test@example.net");
    await element(by.model("confirmation_email")).sendKeys("test@example.net");
    await element.all(by.xpath(".//*[text()='Anticorruption']")).get(0).click();
    await element(by.cssContainingText("button", "Complete")).click();
    await browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='Success!']"));
  });
});

describe("admin disable signup", function() {
  it("should disable signup", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/sites");
    await element(by.cssContainingText("a", "Options")).click();
    await element(by.model("resources.node.enable_signup")).click();
    await element.all(by.cssContainingText("button", "Save")).last().click();
  });
});
