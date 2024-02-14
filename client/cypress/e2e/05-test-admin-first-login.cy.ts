describe("admin login", () => {
  it("should login as admin", () => {
    cy.login_admin();

    cy.visit("#/admin/preferences");
    cy.get("#account_recovery_key").click();
    cy.get("[name='secret']").type(Cypress.env("user_password"));
    cy.get("#confirm").click();
    cy.get('src-encryption-recovery-key').should('exist');
    cy.get("#close").click();

    cy.logout();
  });
});
