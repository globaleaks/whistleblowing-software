describe("admin disable submissions", () => {
  it("should disable submission", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("button", "Advanced").click();

    cy.get('input[name="disable_submissions"]').click();
    cy.contains("button", "Save").click();

    cy.logout();
    cy.visit("/#/");
  });
});

describe("admin configure custom texts", () => {
  it("should perform custom texts configuration", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("button", "Text customization").click();

    cy.get('select[name="vars.text_to_customize"]').select("Submissions disabled");

    cy.get("[name='vars.custom_text']").clear().type("Whistleblowing disabled");

    cy.get("#addCustomTextButton").click();

    cy.reload();
    cy.visit("/#/");
    cy.contains("button", "Whistleblowing disabled").should("exist");
    cy.contains("button", "Submissions disabled").should("not.exist");

    cy.visit("/#/admin/settings");
    cy.contains("button", "Text customization").click();

    cy.get(".deleteCustomTextButton").click();

    cy.logout();

    cy.reload();
    cy.visit("/#/");
    cy.reload();
    cy.contains("button", "Whistleblowing disabled").should("not.exist");
    cy.contains("button", "Submissions disabled").should("exist");
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
    cy.waitForLoader()

    cy.visit("/#/");
    cy.contains("button", "File a report").should("be.visible");
  });
});