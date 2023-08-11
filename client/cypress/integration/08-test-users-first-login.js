describe("Recipient first login", () => {
  it("should require password change upon successful authentication", () => {
    cy.login_receiver("Recipient", Cypress.env("init_password"), "/login", true);
  });

  it("should be able to change password from the default one", () => {
    cy.get("[data-ng-model='changePasswordArgs.password']").type(Cypress.env("user_password"));
    cy.get("[data-ng-model='changePasswordArgs.confirm']").type(Cypress.env("user_password"));
    cy.get('[data-ng-click="changePassword()"]').click();
    cy.waitForUrl("/recipient/home");
    cy.logout();
  });

  it("should be able to login with the new password", () => {
    cy.login_receiver();
  });

  it("should be able to retrieve the account recovery key", () => {
      cy.login_receiver("Recipient", Cypress.env("user_password"), "/login", true);
      cy.waitForUrl("/recipient");
      cy.visit("/recipient/preferences");
      cy.takeScreenshot("user/preferences.png");
      cy.contains("button", "Account recovery key").click();
      cy.get("[data-ng-model='secret']").type(Cypress.env("user_password"));
      cy.contains("button", "Confirm").click();
      cy.takeScreenshot("user/recoverykey.png");
      cy.contains("button", "Close").click();
      cy.get("[data-ng-model='resources.preferences.two_factor']").click();
      cy.takeScreenshot("user/2fa.png");
      cy.contains("button", "Close").click();
  });

  if (Cypress.env("pgp")) {
    it("should be able to load his/her public PGP key", () => {
      cy.addPublicKey(pgp_key_path);
      cy.takeScreenshot("user/pgp.png");
    });
  }

  it("should be able to see the interface for changing the authentication password", () => {
    cy.contains("a", "Password").click();
    cy.takeScreenshot("user/password.png");
    cy.logout();
  });
});

describe("Recipient2 first login", () => {
  it("should require password change upon successful authentication", () => {
    cy.login_receiver("Recipient2", Cypress.env("init_password"), "/login", true);
  });

  it("should be able to change password from the default one", () => {
    cy.get('[data-ng-model="changePasswordArgs.password"]').type(Cypress.env("user_password"));
    cy.get('[data-ng-model="changePasswordArgs.confirm"]').type(Cypress.env("user_password"));
    cy.get('[data-ng-click="changePassword()"]').click();
    cy.url().should("include", "/recipient/home");
  });

  it("should be able to change again the password setting it to the default one", () => {
    cy.get("#PreferencesLink").click();
    cy.contains("a", "Password").click();
    cy.get('[data-ng-model="changePasswordArgs.current"]').type(Cypress.env("user_password"));
    cy.get('[data-ng-model="changePasswordArgs.password"]').type(Cypress.env("init_password"));
    cy.get('[data-ng-model="changePasswordArgs.confirm"]').type(Cypress.env("init_password"));
    cy.get('[data-ng-click="changePassword()"]').click();
    cy.logout();
  });
});


describe("Custodian first login", () => {
  it("should require password change upon successful authentication", () => {
    cy.login_custodian("Custodian", Cypress.env("init_password"), "/login", true);
  });

  it("should be able to change password from the default one", () => {
    cy.get('[data-ng-model="changePasswordArgs.password"]').type(Cypress.env("user_password"));
    cy.get('[data-ng-model="changePasswordArgs.confirm"]').type(Cypress.env("user_password"));
    cy.get('[data-ng-click="changePassword()"]').click();
    cy.url().should("include", "/custodian/home");
    cy.logout();
  });
});

describe("Admin2 first login", () => {
  it("should require password change upon successful authentication", () => {
    cy.login_custodian("Admin2", Cypress.env("init_password"), "/login", true);
  });

  it("should be able to change password from the default one", () => {
    cy.get('[data-ng-model="changePasswordArgs.password"]').type(Cypress.env("user_password"));
    cy.get('[data-ng-model="changePasswordArgs.confirm"]').type(Cypress.env("user_password"));
    cy.get('[data-ng-click="changePassword()"]').click();
    cy.url().should("include", "/admin/home");
    cy.logout();
  });
});

