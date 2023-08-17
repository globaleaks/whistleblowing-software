describe("admin login", () => {
  it("should login as admin", () => {
    cy.login_admin();

    cy.visit("/#/admin/preferences");
    cy.contains("button", "Account recovery key").click();
    cy.get("[data-ng-model='secret']").type(Cypress.env("user_password"));
    cy.contains("button", "Confirm").click();
    cy.contains("button", "Close").click();

    cy.logout();
  });
});
