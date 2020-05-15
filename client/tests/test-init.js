describe("init", () => {
  it("should load the app", async () => {
    var remote = require("selenium-webdriver/remote");
    await browser.setFileDetector(new remote.FileDetector());

    await browser.get("/");
  });
});
