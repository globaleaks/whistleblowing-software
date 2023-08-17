describe("admin configure custom texts", () => {
  it("should perform custom texts configuration", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("a", "Text customization").click();

    // Find the select element and select the option "Submissions disabled"
    cy.get('select[data-ng-model="vars.text_to_customize"]').select("Submissions disabled");

    // Find the input field and set the custom text
    cy.get("[data-ng-model='vars.custom_text']").clear().type("Whistleblowing disabled");

    // Save settings
    cy.get("#addCustomTextButton").click();
    cy.logout();

    cy.visit("/#/");
    cy.contains("button", "Whistleblowing disabled").should("exist");
    cy.contains("button", "Submissions disabled").should("not.exist");

    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("a", "Text customization").click();

    // Save settings (delete the custom text)
    cy.get(".deleteCustomTextButton").click();

    cy.logout();

    cy.visit("/#/");
    cy.contains("button", "Whistleblowing disabled").should("not.exist");
    cy.contains("button", "Submissions disabled").should("exist");
  });
});
