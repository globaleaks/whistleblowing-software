describe("admin login", function() {
  it("should login as admin", async function() {
    await browser.gl.utils.login_admin();
  });
});
