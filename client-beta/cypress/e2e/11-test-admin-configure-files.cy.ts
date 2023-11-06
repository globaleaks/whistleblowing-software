describe("Admin configure custom CSS", () => {
  it("should be able to enable the file upload", () => {
    cy.login_admin();

    cy.visit("#/admin/settings");

    cy.contains("button", "Files").click();

    cy.get("[name='authenticationData.session.permissions.can_upload_files']").should("not.be.checked").click();
    cy.get(".modal").should("be.visible");
    cy.get(".modal [type='password']").type("wrongpassword");
    cy.get(".modal .btn-primary").click();
    cy.get(".modal").should("be.visible");
    cy.wait(500)
    cy.get(".modal [type='password']").type(Cypress.env("user_password"));
    cy.get(".modal .btn-primary").click();
    cy.get("[name='authenticationData.session.permissions.can_upload_files']").should("be.checked");
  });

  it("should be able to configure a custom CSS", () => {
    cy.login_admin();
    cy.visit("#/admin/settings");
    cy.contains("button", "Files").click();

    cy.get("[name='authenticationData.session.permissions.can_upload_files']").should("not.be.checked").click();
    cy.get(".modal").should("be.visible");
    cy.get(".modal [type='password']").type(Cypress.env("user_password"));
    cy.get(".modal .btn-primary").click();

    const customCSSFile = "files/style.css";
    cy.fixture(customCSSFile).then((fileContent) => {
      cy.get("div.uploadfile.file-css input").then(($input) => {
        const inputElement = $input[0] as HTMLInputElement;
        const blob = new Blob([fileContent], { type: "text/css" });
        const testFile = new File([blob], customCSSFile, { type: "text/css" });
        const dataTransfer = new DataTransfer();

        dataTransfer.items.add(testFile);
        inputElement.files = dataTransfer.files;
        cy.wrap($input).trigger("change", { force: true });
      });
    });
    cy.contains("label", "Project name").should("be.visible");
  });

  it("should upload a file and make it available for download and deletion", () => {

    cy.login_admin();
    cy.visit("#/admin/settings");
    cy.contains("button", "Files").click();

    cy.get("[name='authenticationData.session.permissions.can_upload_files']").should("not.be.checked").click();
    cy.get(".modal").should("be.visible");
    cy.get(".modal [type='password']").type(Cypress.env("user_password"));
    cy.get(".modal .btn-primary").click();

    const customFile = "files/documentation.pdf";
    cy.fixture(customFile).then((fileContent) => {
      cy.get("div.file-custom input").then(($input) => {
        const inputElement = $input[0] as HTMLInputElement;
        const blob = new Blob([fileContent], { type: "text/css" });
        const testFile = new File([blob], customFile, { type: "text/css" });
        const dataTransfer = new DataTransfer();

        dataTransfer.items.add(testFile);
        inputElement.files = dataTransfer.files;
        cy.wrap($input).trigger("change", { force: true });
      });
    });

    cy.waitForLoader()
    cy.contains("button", "Files").click();
    cy.get('table#fileList').contains('td', 'documentation').should('be.visible');
    cy.get("#fileList").contains("Delete").click();

    cy.waitForLoader()
    cy.contains("button", "Files").click();
    cy.get('table#fileList').contains('td', 'documentation').should('not.exist');
  });


  it("should be able to disable the file upload", () => {

    cy.login_admin();
    cy.visit("#/admin/settings");
    cy.contains("button", "Files").click();

    cy.get("[name='authenticationData.session.permissions.can_upload_files']").should("not.be.checked").click();
    cy.get(".modal").should("be.visible");
    cy.get(".modal [type='password']").type(Cypress.env("user_password"));
    cy.get(".modal .btn-primary").click();

    cy.get("[name='authenticationData.session.permissions.can_upload_files']").should("be.checked").click();
    cy.get("[name='authenticationData.session.permissions.can_upload_files']").should("not.be.checked");

    cy.logout();
  });
});
