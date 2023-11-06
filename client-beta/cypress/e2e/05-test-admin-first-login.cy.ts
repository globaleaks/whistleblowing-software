describe("admin login", () => {
  it("should login as admin", () => {
    cy.login_admin();

    cy.visit("#/admin/preferences");
    cy.contains("button", "Account recovery key").click();
    cy.get("[name='secret']").type(Cypress.env("user_password"));
    cy.contains("button", "Confirm").click();
    cy.get('src-encryption-recovery-key').should('exist');
    cy.contains("button", "Close").should("be.visible").click();

    cy.logout();
  });
});
