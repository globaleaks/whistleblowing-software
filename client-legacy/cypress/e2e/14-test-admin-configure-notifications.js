describe("admin configure mail", () => {
  it("should configure mail", () => {
    cy.login_admin();
    cy.visit("/#/admin/notifications");

    cy.get("[data-ng-model='resources.notification.tip_expiration_threshold']").clear().type("24");

    // save settings
    cy.contains("[data-ng-click='Utils.update(resources.notification)']", "Save").click();

    cy.logout();
  });
});
