describe("Admin Enable Signup", function() {
  it("should enable signup", function() {
    cy.visit("/#/login");
    cy.login_admin();

    cy.visit("/#/admin/sites");
    cy.contains("a", "Options").should('be.visible').click();
    cy.get('input[data-ng-model="resources.node.rootdomain"]').type("domain.tld");
    cy.get('input[data-ng-model="resources.node.enable_signup"]').click();
    cy.get('select[data-ng-model="resources.node.mode"]').select("DEMO");
    cy.takeScreenshot("admin/signup_configuration");
    cy.get('i.fa-solid.fa-check').click();

    cy.logout();
  });
});

describe("User Perform Signup", function() {
  it("should perform signup", function() {
    cy.visit("/#/");

    cy.takeScreenshot("admin/signup_form");

    cy.get('input[data-ng-model="signup.subdomain"]').type("test");
    cy.get('input[data-ng-model="signup.name"]').type("Name");
    cy.get('input[data-ng-model="signup.surname"]').type("Surname");
    cy.get('input[data-ng-model="signup.email"]').type("test@example.net");
    cy.get('input[data-ng-model="confirmation_email"]').type("test@example.net");
    cy.contains("button", "Proceed").click();
    cy.contains("Success!", { timeout: 10000 }).should("be.visible");
    });
});

describe("Admin Disable Signup", function() {
  it("should disable signup", function() {
    cy.login_admin();

    cy.visit("/#/admin/sites");
    cy.contains("a", "Options").click();
    cy.get('input[data-ng-model="resources.node.enable_signup"]').click();
    cy.get('i.fa-solid.fa-check').click();

    cy.logout();
    cy.visit("/#/");
  });
});
