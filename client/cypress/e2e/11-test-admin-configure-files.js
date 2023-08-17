describe("Admin configure custom CSS", () => {
  it("should be able to configure a custom CSS", () => {
    cy.login_admin();

    cy.visit("/#/admin/settings");

    cy.contains("a", "Files").click();

    cy.get(".custom-switch").should("not.be.checked").click();

    cy.get(".modal").should("be.visible");

    cy.get(".modal [type='password']").type("wrongpassword");
    cy.get(".modal .btn-primary").click();

    cy.get(".modal").should("be.visible");

    cy.get(".modal [type='password']").type(Cypress.env("user_password"));
    cy.get(".modal .btn-primary").click();

    cy.get(".custom-switch input").should("be.checked");

    const customCSSFile = "files/style.css";
    cy.fixture(customCSSFile).then(fileContent => {
      cy.get("div.uploadfile.file-css input").then(input => {
        const blob = new Blob([fileContent], { type: "text/css" });
        const testFile = new File([blob], customCSSFile, { type: "text/css" });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(testFile);
        input[0].files = dataTransfer.files;
        cy.wrap(input).trigger("change", { force: true });
      });
    });

    cy.contains("label", "Logo").should("be.visible");

    cy.contains("a", "Files").click().debug();
    const customFile = "files/documentation.pdf";
    cy.fixture(customFile).then(fileContent => {
      cy.get("div.file-custom input").then(input => {
        const blob = new Blob([fileContent], { type: "application/pdf" });
        const testFile = new File([blob], customFile, { type: "application/pdf" });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(testFile);
        input[0].files = dataTransfer.files;
        cy.wrap(input).trigger("change", { force: true });
        cy.contains("label", "Logo").should("be.visible");
        cy.contains("a", "Files").click();
        cy.get("#fileList").contains("Delete").click();
        cy.contains("label", "Logo").should("be.visible");
      });
    });

    cy.contains("a", "Files").click();
    cy.get(".custom-switch").click();
    cy.get(".custom-switch input").should("not.be.checked");

    cy.logout();
  });
});
