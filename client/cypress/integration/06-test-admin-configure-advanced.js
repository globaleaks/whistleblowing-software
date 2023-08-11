describe("admin configure advanced settings", () => {
  it("should perform main configuration", () => {
    cy.login_admin();
    cy.visit("/admin/settings");
    cy.contains("a", "Advanced").click();

    cy.get("[data-ng-model='resources.node.disable_privacy_badge']").click();
    cy.get("[data-ng-model='resources.node.enable_custodian']").click();

    if (Cypress.env('pgp')) {
      cy.get("[data-ng-model='resources.node.pgp']").click();
    }

    cy.get("[data-ng-model='resources.node.viewer']").click();
    cy.get("[data-ng-click='updateNode()']").last().click();
    cy.waitForLoader();

  });
});

describe("admin disable submissions", () => {
  it("should disable submission", () => {

    cy.contains("a", "Advanced").click();

    cy.get("[data-ng-model='resources.node.disable_submissions']").click();
    cy.get("[data-ng-click='updateNode()']").last().click();

    cy.get("[data-ng-model='resources.node.disable_submissions']").should("be.visible").should("be.checked");

    cy.logout();

    cy.visit("/");
    cy.contains("span", "Submissions disabled").should("be.visible");

    cy.login_admin();
    cy.visit("/admin/settings");
    cy.contains("a", "Advanced").click();

    cy.get("[data-ng-model='resources.node.disable_submissions']").click();
    cy.get("[data-ng-click='updateNode()']").last().click();

    cy.get("[data-ng-model='resources.node.disable_submissions']").should(
      "not.be.checked"
    );

    cy.logout();

    cy.waitForUrl('/login');
    cy.visit("/");
    cy.contains("button", "File a report").should("be.visible");
  });
});

describe("Validating custom support url", () => {
  it("Enter custom support url and browser", () => {

    cy.login_admin();
    cy.visit("/admin/settings");
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

    cy.get("#SupportLink").click();

    cy.window().then((win) => {
      const newUrl = win.location.href;
      expect(newUrl).to.equal("https://www.globaleaks.org/");
    });
  });
});

describe("Should browser opens a pop while clicking the support icon", () => {
  it("should open a pop-up modal", () => {

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
  });
});
