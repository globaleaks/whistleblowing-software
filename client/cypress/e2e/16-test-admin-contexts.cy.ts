describe("admin configure, add, and delete contexts", () => {
  it("should configure an existing context", () => {
    cy.visit("/");
    cy.login_admin();

    cy.visit("#/admin/contexts");

    cy.get("#context-0").within(() => {
      cy.contains("Edit").click();

      for (let i = 0; i <= 2; i++) {
        cy.get(".add-receiver-btn").click();
        cy.get('ng-select[name="selected.value"]').click();
        if (i === 0) {
          cy.get('ng-select[name="selected.value"]').contains('Recipient').click();
        } else {
          cy.get('ng-select[name="selected.value"]').contains(`Recipient${i + 1}`).click();
        }
      }

      cy.contains("Advanced").click();
      cy.contains("Save").click();
    });
  });

  it("should add new contexts", () => {
    cy.visit("/");
    cy.login_admin();

    cy.visit("#/admin/contexts");
    const add_context = async (context_name:string) => {
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
    cy.get('button:contains("Delete")').last().click();
    cy.get("#modal-action-ok").click();

    cy.logout();
  });
});
