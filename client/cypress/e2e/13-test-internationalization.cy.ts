describe("Whistleblower Navigate Home Page", () => {
  it("should see page properly internationalized", () => {

    cy.visit("#/?lang=en");
    cy.get('div').should('not.contain', 'TEXT1_IT');
    cy.get('div').should('not.contain', 'TEXT2_IT');

    cy.visit("#/?lang=it");
    cy.contains("div", "TEXT1_IT").should("exist");
    cy.contains("div", "TEXT2_IT").should("exist");
  });
});
