describe("user login", function () {
  it("should enable users to request password reset", function () {
    cy.visit("/#/login");
    cy.takeScreenshot("user/login");
    cy.contains("a", "Forgot password?").click();
    cy.waitForUrl("/login/passwordreset");
    cy.takeScreenshot("user/password_reset_1");
    cy.get('[name="username"]').type("admin");
    cy.contains("button", "Submit").click();
    cy.waitForUrl("/login/passwordreset/requested");
    cy.takeScreenshot("user/password_reset_2");
  });
});
