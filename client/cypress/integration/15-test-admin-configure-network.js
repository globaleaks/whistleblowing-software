describe("admin configure network", () => {

  let files = {};
  before(() => {
    files = {
      key: "../backend/globaleaks/tests/data/https/valid/key.pem",
      cert: "../backend/globaleaks/tests/data/https/valid/cert.pem",
      chain: "../backend/globaleaks/tests/data/https/valid/chain.pem",
    };
  });

  beforeEach(() => {
    cy.login_admin();
    cy.waitForLoader();
    cy.visit("/admin/network");
  });

  it("should be able to configure https", () => {
    cy.contains("a", "HTTPS").click();

    cy.get('[name="hostname"]').clear().type("domain.tld");
    cy.get('button:contains("Save")').first().click();

    cy.waitForLoader();
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

    cy.readExternalFile(files.key).then(keyContent => {
      cy.get("div.card.key input[type=file]").attachFile({
        fileContent: keyContent,
        fileName: "key.pem",
        mimeType: "application/x-pem-file"
      });
    });

    // Attach cert file
    cy.readExternalFile(files.cert).then(certContent => {
      cy.get("div.card.cert input[type=file]").attachFile({
        fileContent: certContent,
        fileName: "cert.pem",
        mimeType: "application/x-pem-file"
      });
    });

    // Attach chain file
    cy.readExternalFile(files.chain).then(chainContent => {
      cy.get("div.card.chain input[type=file]").attachFile({
        fileContent: chainContent,
        fileName: "chain.pem",
        mimeType: "application/x-pem-file"
      });
    });

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
