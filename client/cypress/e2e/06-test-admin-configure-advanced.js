describe("admin configure advanced settings", () => {
  it("should perform main configuration", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("a", "Advanced").click();

    cy.get("[data-ng-model='resources.node.disable_privacy_badge']").click();
    cy.get("[data-ng-model='resources.node.enable_custodian']").click();

    cy.get("[data-ng-click='updateNode()']").last().click();
    cy.waitForLoader();
  });
});

describe("admin disable submissions", () => {
  it("should disable submission", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("a", "Advanced").click();

    cy.get("[data-ng-model='resources.node.disable_submissions']").click();
    cy.get("[data-ng-click='updateNode()']").last().click();

    cy.get("[data-ng-model='resources.node.disable_submissions']").should("be.visible").should("be.checked");

    cy.logout();

    cy.visit("/#/");
    cy.contains("span", "Submissions disabled").should("be.visible");
  });
});

describe("admin enable submissions", () => {
  it("should enable submission", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("a", "Advanced").click();

    cy.get("[data-ng-model='resources.node.disable_submissions']").click();
    cy.get("[data-ng-click='updateNode()']").last().click();

    cy.get("[data-ng-model='resources.node.disable_submissions']").should("be.visible").should("not.be.checked");

    cy.logout();

    cy.visit("/");
    cy.contains("button", "File a report").should("be.visible");
  });
});


describe("Should browser opens a pop while clicking the support icon", () => {
  it("should open a pop-up modal", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("a", "Advanced").click();

    cy.get("[data-ng-model='resources.node.custom_support_url']").clear();
    cy.get("[data-ng-click='updateNode()']").last().click();
    cy.waitForLoader();

    cy.get("[data-ng-model='resources.node.custom_support_url']")
      .invoke("val")
      .should("equal", "");

    cy.get("#SupportLink").click();
    cy.get(".modal").should("be.visible");

    cy.get("[data-ng-model='arg.text']").type("test message");
    cy.get(".modal #modal-action-ok").click();

    cy.contains(
      "Thank you. We will try to get back to you as soon as possible."
    ).should("be.visible");

    cy.get("#modal-action-cancel").click();

    cy.logout();
    cy.waitForUrl('/login');
  });
});

describe("Validating custom support url", () => {
  it("Enter custom support url and browser", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("a", "Advanced").click();

    cy.get("[data-ng-model='resources.node.custom_support_url']").clear();
    cy.get("[data-ng-model='resources.node.custom_support_url']").type(
      "https://www.globaleaks.org/"
    );

    cy.get("[data-ng-click='updateNode()']").last().click();
    cy.contains("a", "Advanced").click();

    cy.get("[data-ng-model='resources.node.custom_support_url']")
      .invoke("val")
      .should("equal", "https://www.globaleaks.org/");
  });
});
