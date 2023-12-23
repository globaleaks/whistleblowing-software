describe("admin configure, add, and delete contexts", () => {
  it("should configure an existing context", () => {
    cy.login_admin();

    cy.visit("/#/admin/contexts");

    cy.get("#context-0").within(() => {
      cy.contains("Edit").click();

      for (let i = 0; i <= 2; i++) {
        cy.get(".add-receiver-btn").click();
        cy.get("#ReceiverContextAdder").find("[data-ng-model='selected.value']").click();
        cy.get(".ui-select-search").type("Recipient");
        cy.get(".ui-select-choices-row-inner span").first().click();
      }

      cy.contains("Advanced").click();

      // Save the results
      cy.contains("Save").click();
    });
  
    const add_context = async (context_name) => {
      cy.get(".show-add-context-btn").click();
      cy.get("[data-ng-model='new_context.name']").type(context_name);
      cy.get("#add-btn").click();
      cy.contains(context_name, { timeout: 10000 }).should("be.visible");
    };

    add_context("Topic A");
    add_context("Topic B");
    add_context("Topic C");

    cy.takeScreenshot("admin/contexts");

    cy.get("button:contains('Delete')").last().click();

    cy.get("#modal-action-ok").click();

    cy.logout();
  });
});
