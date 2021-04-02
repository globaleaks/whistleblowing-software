describe("user login", function() {
  it("should enable users to reques password reset", async function() {
    await browser.get("/#/login");
    await browser.gl.utils.takeScreenshot("user/login.png");
    await element(by.cssContainingText("a", "Forgot password?")).click();
    await browser.gl.utils.waitForUrl("/login/passwordreset");
    await browser.gl.utils.takeScreenshot("user/password_reset_1.png");
    await element(by.model("request.username")).sendKeys("admin");
    await element(by.cssContainingText("button", "Submit")).click();
    await browser.gl.utils.waitForUrl("/login/passwordreset/requested");
    await browser.gl.utils.takeScreenshot("user/password_reset_2.png");
  });
});
