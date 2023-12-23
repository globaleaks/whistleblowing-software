describe("key escrow assignment and revocation", () => {
  it("should assign escrow key to Admin 2", () => {
    cy.login_admin();

    cy.visit("/#/admin/users");

    const user = { name: "Admin2" };
    const path = `form:contains("${user.name}")`;

    cy.get(path).within(() => {
      cy.contains("button", "Edit").click();

      // Toggle key escrow
      cy.get("[data-ng-model='user.escrow']").click();

    });

    cy.get("[data-ng-model='secret']").type(Cypress.env("user_password"));
    cy.contains("button", "Confirm").click();

    cy.logout();
  });
});
