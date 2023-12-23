describe("globaLeaks setup wizard", () => {
  it("should allow the user to setup the wizard", () => {
    cy.visit("/#/wizard");

    cy.contains("h1", "Platform wizard").should("be.visible");

    cy.takeScreenshot("wizard/1");

    cy.get(".ButtonNext").eq(0).click();

    cy.takeScreenshot("wizard/2");

    cy.get('[data-ng-model="wizard.node_name"]').type("GLOBALEAKS");

    cy.get(".ButtonNext").eq(1).click();

    cy.takeScreenshot("wizard/3");

    cy.get('[data-ng-model="wizard.admin_username"]').type("admin");
    cy.get('[data-ng-model="wizard.admin_name"]').type("Admin");
    cy.get('[data-ng-model="wizard.admin_mail_address"]').type("globaleaks-admin@mailinator.com");
    cy.get('[data-ng-model="wizard.admin_password"]').type(Cypress.env('user_password'));
    cy.get('[data-ng-model="admin_check_password"]').type(Cypress.env('user_password'));

    cy.get(".ButtonNext").eq(3).click();
    
    cy.takeScreenshot("wizard/4");

    cy.get('[data-ng-model="wizard.skip_recipient_account_creation"]').click();

    cy.get(".ButtonNext").eq(4).click();

    cy.takeScreenshot("wizard/5");

    cy.get('.tos-agreement-input').click();

    cy.get(".ButtonNext").eq(5).click();

    cy.contains("div", "Congratulations!").should("exist");

    cy.get(".ButtonNext").eq(6).click();

    cy.takeScreenshot("wizard/6");

    cy.url().should('include', '/admin/home');

    cy.logout();
  });
});
