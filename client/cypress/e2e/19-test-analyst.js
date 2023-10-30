describe("Analyst", () => {
  it("should be able to visualize statistics", () => {
    cy.login_analyst();
    cy.visit("/#/analyst/statistics");
    cy.wait(2000);
    cy.takeScreenshot("analyst/statistics");
    cy.logout();
  });
});
