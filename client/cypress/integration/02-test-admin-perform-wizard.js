describe("globaLeaks setup wizard", () => {
  it("should allow the user to setup the wizard", () => {
    cy.visit("/wizard");

    cy.takeScreenshot("wizard/1.png");

    cy.get(".ButtonNext").eq(0).click();

    cy.takeScreenshot("wizard/2.png");

    cy.get('[data-ng-model="wizard.node_name"]').type("GLOBALEAKS");

    cy.get(".ButtonNext").eq(1).click();

    cy.takeScreenshot("wizard/3.png");

    cy.get('[data-ng-model="wizard.admin_username"]').type("admin");
    cy.get('[data-ng-model="wizard.admin_name"]').type("Admin");
    cy.get('[data-ng-model="wizard.admin_mail_address"]').type("globaleaks-admin@mailinator.com");
    cy.get('[data-ng-model="wizard.admin_password"]').type(Cypress.env('user_password'));
    cy.get('[data-ng-model="admin_check_password"]').type(Cypress.env('user_password'));

    cy.get(".ButtonNext").eq(3).click();

    cy.get('[data-ng-model="wizard.skip_recipient_account_creation"]').click();

    cy.get(".ButtonNext").eq(4).click();

    cy.get('.tos-agreement-input').click();

    cy.takeScreenshot("wizard/5.png");

    cy.get(".ButtonNext").eq(5).click();

    cy.takeScreenshot("wizard/6.png");

    cy.contains("button", "Proceed").click();

    cy.url().should('include', '/admin/home');

    cy.logout();
  });
});
