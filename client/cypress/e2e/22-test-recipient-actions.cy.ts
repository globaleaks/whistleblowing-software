describe("recipient admin tip actions", () => {
  it("should revoke and grant access to reports", function () {
    cy.login_receiver();

    cy.visit("/#/recipient/reports");
    cy.get("#tip-0").first().click();

    cy.get("#tip-action-revoke-access").should('be.visible', { timeout: 10000 }).click();
    cy.get('[data-cy="reciever_selection"]').click();
    cy.get('.ng-dropdown-panel').should('be.visible');
    cy.get('[data-cy="reciever_selection"]').click();
    cy.get("#modal-action-ok").click();

    cy.get("#tip-action-grant-access").should('be.visible', { timeout: 10000 }).click();
    cy.get('[data-cy="reciever_selection"]').click();
    cy.get('.ng-dropdown-panel').should('be.visible');
    cy.get('[data-cy="reciever_selection"]').click();
    cy.get("#modal-action-ok").click();

    cy.logout();
  });
  it("should close and reopen reports", function () {
    cy.login_receiver();

    cy.visit("/#/recipient/reports");
    cy.get("#tip-0").first().click();

    cy.get("#tip-action-change-status").click();
    cy.get('#assignSubmissionStatus', { timeout: 10000 }).select(1);
    cy.get('textarea[name="reason"]').type("This is a close status illatest motivation");
    cy.get("#modal-action-ok").click();
    cy.get("#tip-action-reopen-status").click();
    cy.get('textarea[name="motivation"]').type("This is a Reopen status test motivation");
    cy.get("#modal-action-ok").click();

    cy.logout();
  });
  it("recipient should file a report on behalf of whistleblower", function () {
    cy.login_receiver();

    cy.visit("/#/recipient/reports");
    cy.get("#tip-action-open-new-tab").click();
    cy.visit("/#/recipient/reports");

    cy.logout();
  });

  it("should set a reminder date for reports", function () {
    cy.login_receiver();

    cy.visit("/#/recipient/reports");
    cy.get("#tip-0").first().click();
    cy.get("#tip-action-reminder").click();
    cy.get('.modal').should('be.visible');

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const formattedDate = tomorrow.toISOString().split('T')[0];

    cy.get('input[name="dp"]').click().clear();
    cy.get('input[name="dp"]').click().type(formattedDate);
    cy.get('#modal-action-ok').click();

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
  it("should change sub-status for reports", function () {
    cy.login_receiver();
    cy.visit("/#/recipient/reports");
    cy.get("#tip-0").first().click();
    cy.get("#tip-action-change-status").click();
    cy.get('#assignSubmissionStatus', { timeout: 10000 }).select(0);
    cy.get('textarea[name="reason"]').type("This is a test motivation");
    cy.get("#modal-action-ok").click();
    cy.logout();
  });
});
