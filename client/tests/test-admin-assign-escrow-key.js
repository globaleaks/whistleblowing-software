describe("key escrow assignment and revocation", function() {
  it("should assign escrow key to Admin 2", async function() {
    await browser.gl.utils.login_admin();

    for (var i = 0; i<2; i++) {
      await browser.setLocation("admin/users");

      var user = { name: "Admin2" };
      var path = "//form[contains(.,\"" + user.name + "\")]";

      var editUsrForm = element(by.xpath(path));

      await editUsrForm.element(by.cssContainingText("button", "Edit")).click();

      // Toggle key escrow
      await element(by.model("user.escrow")).click();
    }

    await browser.gl.utils.logout();
  });
});
