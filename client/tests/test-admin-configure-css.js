describe("Admin configure custom CSS", function() {
  it("should be able to enable the file upload", async function() {
    await browser.gl.utils.login_admin();

    await browser.setLocation("admin/settings");
    await browser.gl.utils.waitUntilPresent(by.cssContainingText("a", "Theme customization"));

    await element(by.cssContainingText("a", "Theme customization")).click();
    const customSwitch = await element(by.css(".custom-switch"));
    customSwitch.click();
    expect(await element(by.css(".modal")).isDisplayed()).toBeTruthy();
  });

  it("should be able show a model on toggle button clicked", async function() {
    expect(await element(by.css(".modal")).isDisplayed()).toBeTruthy();
  });

  it("should show the model again if wrong password is enterd", async function() {
    const modelInput = await element(by.css(".modal [type='password']"));

    // sending wrong password
    await modelInput.sendKeys("admin");
    await element(by.css(".modal .btn-primary")).click();

    expect(await element(by.css(".modal")).isDisplayed()).toBeTruthy();
  });

  it("should close the model  if password is right", async function() {
    const modelInput = await element(by.css(".modal [type='password']"));
    
    // sending right password
    await modelInput.sendKeys(browser.gl.utils.vars.user_password);
    await element(by.css(".modal .btn-primary")).click();

    const customSwitch = await element(by.css(".custom-switch input"));
    
    expect(customSwitch.isSelected()).toBeTruthy();
  });

  it("should be able to configure a custom CSS", async function() {
    var customCSSFile = browser.gl.utils.makeTestFilePath("style.css");

    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/settings");

    await browser.gl.utils.waitUntilPresent(by.cssContainingText("a", "Theme customization"));

    await element(by.cssContainingText("a", "Theme customization")).click();

    await element(by.css("div.uploadfile.file-css input")).sendKeys(customCSSFile);

    await browser.gl.utils.waitUntilPresent(by.cssContainingText("label", "Project name"));

    await browser.gl.utils.logout();
  });
});
