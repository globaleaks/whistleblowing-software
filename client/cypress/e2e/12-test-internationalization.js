describe("Whistleblower Navigate Home Page", () => {
  it("should see page properly internationalized", () => {
    // Visit the page with lang=en
    cy.visit("/#/?lang=en");

    // Check that TEXT1_IT is not present
    cy.contains("div", "TEXT1_IT").should("not.exist");

    // Check that TEXT2_IT is not present
    cy.contains("div", "TEXT2_IT").should("not.exist");

    // Visit the page with lang=it
    cy.visit("/#/?lang=it");

    // Check that TEXT1_IT is present
    cy.contains("div", "TEXT1_IT").should("exist");

    // Check that TEXT2_IT is present
    cy.contains("div", "TEXT2_IT").should("exist");
  });
});
