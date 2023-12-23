describe("admin configure network", () => {
  beforeEach(() => {
    cy.login_admin();
    cy.visit("/#/admin/network");
  });

  it("should be able to configure https", () => {
    cy.contains("button", "HTTPS").click();

    cy.get('[name="hostname"]').clear().type("localhost");
    cy.get('button:contains("Save")').first().click();

    cy.get("#HTTPSManualMode").click();
    cy.contains("button", "Generate").click();
    cy.waitForLoader();
    cy.get("#csrGen").click();
    cy.get('[name="country"]').type("IT");
    cy.get('[name="province"]').type("Milano");
    cy.get('[name="city"]').type("Lombardia");
    cy.get('[name="company"]').type("GlobaLeaks");
    cy.get('[name="email"]').type("admin@globaleaks.org");
    cy.get("#csrSubmit").click();

    cy.get("#deleteKey").click();
    cy.wait(500);
    cy.get("#modal-action-ok").click();
    cy.get("#deleteKey").should("not.exist");
    cy.wait(500);
    cy.get("#HTTPSManualMode").click();

    cy.get("div.card.key input[type=file]").selectFile({
      contents: "../backend/globaleaks/tests/data/https/valid/key.pem",
      fileName: "key.pem",
      mimeType: "application/x-pem-file"
    }, {"force": true});

    cy.get("div.card.cert input[type=file]").selectFile({
      contents: "../backend/globaleaks/tests/data/https/valid/cert.pem",
      fileName: "cert.pem",
      mimeType: "application/x-pem-file"
    }, {"force": true});

    cy.get("div.card.chain input[type=file]").selectFile({
      contents: "../backend/globaleaks/tests/data/https/valid/chain.pem",
      fileName: "chain.pem"
    }, {"force": true});

    cy.get("#deleteChain").click();
    cy.get("#modal-action-ok").click();

    cy.get("#deleteCert").click();
    cy.get("#modal-action-ok").click();

    cy.wait(500);
    cy.get("#deleteKey").click();
    cy.get("#modal-action-ok").click();
    cy.logout();
  });

  it("should configure url redirects", () => {
    cy.contains("button", "URL redirects").first().click();
    for (let i = 0; i < 3; i++) {
      cy.get('[name="path1"]').type(`yyyyyyyy-${i}`);
      cy.get('[name="path2"]').type("xxxxxxxx");
      cy.contains("button", "Add").click();
      cy.get("button:contains('Delete')").first().click();
    }
    cy.logout();
  });
});
