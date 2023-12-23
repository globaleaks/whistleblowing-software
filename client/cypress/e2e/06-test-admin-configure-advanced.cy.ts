describe("admin configure advanced settings", () => {
  it("should perform main configuration", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("button", "Advanced").click();
    cy.get('input[name="enable_custom_privacy_badge"]').click();
    cy.get('input[name="enable_custodian"]').click();
    cy.get('input[name="viewer"]').click();
    cy.contains("button", "Save").click();
  });
});

describe("admin disable submissions", () => {
  it("should disable submission", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("button", "Advanced").click();

    cy.get('input[name="disable_submissions"]').click();
    cy.contains("button", "Save").click();

    cy.waitForLoader();
    cy.contains("button", "Advanced").click();

    cy.get('input[name="disable_submissions"]').should("be.visible").should("be.checked");
    cy.logout();
    cy.waitForLoader()
    cy.visit("/#/");
    cy.contains("span", "Submissions disabled").should("be.visible");

  });
});

describe("admin enable submissions", () => {
  it("should enable submission", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("button", "Advanced").click();

    cy.get('input[name="disable_submissions"]').click();
    cy.contains("button", "Save").click();

    cy.waitForLoader();
    cy.contains("button", "Advanced").click();

    cy.get('input[name="disable_submissions"]').should("be.visible").should("not.be.checked");
    cy.logout();
    cy.waitForLoader();

    cy.visit("/#/");
    cy.contains("button", "File a report").should("be.visible");
  });
});

describe("Should browser opens a pop while clicking the support icon", () => {
  it("should open a pop-up modal", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("button", "Advanced").click();

    cy.get('input[name="customSupportURL"]').clear();

    cy.contains("button", "Save").click();
    cy.contains("button", "Advanced").click();

    cy.get('input[name="customSupportURL"]')
      .invoke("val")
      .should("equal", "");

    cy.get("#SupportLink").click();
    cy.get(".modal").should("be.visible");

    cy.get('textarea[name="message"]').type("test message");
    cy.get(".modal #modal-action-ok").click();

    cy.contains(
      "Thank you. We will try to get back to you as soon as possible."
    ).should("be.visible");

    cy.get('#modal-action-cancel').should('be.visible').click();
    cy.logout();
    cy.waitForUrl('/login');
  });
});

describe("Validating custom support url", () => {
  it("Enter custom support url and browser", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("button", "Advanced").click();

    cy.get('input[name="customSupportURL"]').clear();
    cy.get('input[name="customSupportURL"]').type(
      "https://www.globaleaks.org/"
    );

    cy.contains("button", "Save").click();
    cy.waitForLoader();
    cy.contains("button", "Advanced").click();

    cy.get('input[name="customSupportURL"]')
      .invoke("val")
      .should("equal", "https://www.globaleaks.org/");
    cy.logout();

  });
});
