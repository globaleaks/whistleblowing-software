describe("admin configure, add, and delete contexts", () => {
  it("should configure an existing context", () => {
    cy.visit("/");
    cy.login_admin();

    cy.visit("#/admin/contexts");

    cy.get("#context-0").within(() => {
      cy.get("#edit_context").click();

      for (let i = 0; i <= 2; i++) {
        cy.get(".add-receiver-btn").click();
        cy.get('ng-select[name="selected.value"]').click();
        if (i === 0) {
          cy.get('ng-select[name="selected.value"]').contains('Recipient').click();
        } else {
          cy.get('ng-select[name="selected.value"]').contains(`Recipient${i + 1}`).click();
        }
      }

      cy.get("#advance_context").click();
      cy.get("#save_context").click();
    });
  });

  it("should add new contexts", () => {
    cy.visit("/");
    cy.login_admin();

    cy.visit("#/admin/contexts");
    const add_context = async (context_name: string) => {
      cy.get(".show-add-context-btn").click();
      cy.get("[name='new_context.name']").type(context_name);
      cy.get("#add-btn").click();
      cy.contains(context_name, { timeout: 10000 }).should("be.visible");
    };

    add_context("Topic A");
    add_context("Topic B");
    add_context("Topic C");

    cy.takeScreenshot("admin/contextstest-admin-contexts.png");
  });

  it("should delete existing contexts", () => {
    cy.visit("/");
    cy.login_admin();

    cy.visit("#/admin/contexts");
    cy.get("[name='delete_context']").last().click();
    cy.get("#modal-action-ok").click();

    cy.logout();
  });

  it("should add new status and sub-status in the admin section", () => {
    cy.login_admin();

    cy.visit("/#/admin/casemanagement");
    cy.get(".config-section").should("be.visible");
    cy.get(".show-add-user-btn").click();
    cy.get(".addSubmissionStatus").should("be.visible");
    cy.get('input[name="name"]').type("Partial");
    cy.get("#add-btn").click();
    cy.get(".config-section").contains("Partial").should("be.visible").click();
    cy.get("#add-sub-status").click();
    cy.get('input[name="label"]').type("closed");
    cy.get("#add-submission-sub-status").click();

    cy.logout();
  });
});
