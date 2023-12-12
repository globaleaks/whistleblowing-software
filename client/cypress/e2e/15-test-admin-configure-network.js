describe("admin configure network", () => {
  beforeEach(() => {
    cy.login_admin();
    cy.waitForLoader();
    cy.visit("/#/admin/network");
  });

  it("should be able to configure https", () => {
    cy.contains("a", "HTTPS").click();

    cy.get('[name="hostname"]').clear().type("127.0.0.1");
    cy.get('button:contains("Save")').first().click();

    cy.get("#HTTPSManualMode").click();

    // Generate key
    cy.get("div.card.key button:contains('Generate')").click();
    cy.waitForLoader();

    // Generate csr
    cy.get("#csrGen").click();
    cy.get('[data-ng-model="csr_cfg.country"]').type("IT");
    cy.get('[data-ng-model="csr_cfg.province"]').type("Milano");
    cy.get('[data-ng-model="csr_cfg.city"]').type("Lombardia");
    cy.get('[data-ng-model="csr_cfg.company"]').type("GlobaLeaks");
    cy.get('[data-ng-model="csr_cfg.email"]').type("admin@globaleaks.org");
    cy.get("#csrSubmit").click();

    cy.get("#deleteKey").click();
    cy.wait(500)
    cy.get("#modal-action-ok").click();
    cy.get("#deleteKey").should("not.exist");
    cy.wait(500);

    cy.get("div.card.key input[type=file]").selectFile({
      contents: "../backend/globaleaks/tests/data/https/valid/key.pem",
      fileName: "key.pem",
      mimeType: "application/x-pem-file"
    }, {"force": true});

    // Attach cert file
    cy.get("div.card.cert input[type=file]").selectFile({
      contents: "../backend/globaleaks/tests/data/https/valid/cert.pem",
      fileName: "cert.pem",
      mimeType: "application/x-pem-file"
    }, {"force": true});

    // Attach chain file
    cy.get("div.card.chain input[type=file]").selectFile({
      contents: "../backend/globaleaks/tests/data/https/valid/chain.pem",
      fileName: "chain.pem"
    }, {"force": true});

    // Delete chain, cert, key
    cy.get("div.card.chain button[id='deleteChain']").click();
    cy.get("#modal-action-ok").click();

    cy.get("div.card.cert button[id='deleteCert']").click();
    cy.get("#modal-action-ok").click();

    cy.wait(500)
    cy.get("div.card.key button[id='deleteKey']").click();
    cy.get("#modal-action-ok").click();
    cy.logout();
  });

  it("should configure url redirects", () => {
    cy.contains("a", "URL redirects").first().click();
    for (let i = 0; i < 3; i++) {
      cy.get('[data-ng-model="new_redirect.path1"]').type(`yyyyyyyy-${i}`);
      cy.get('[data-ng-model="new_redirect.path2"]').type("xxxxxxxx");
      cy.contains("button", "Add").click();
      cy.get("button:contains('Delete')").first().click();
    }
    cy.logout();
  });
});
