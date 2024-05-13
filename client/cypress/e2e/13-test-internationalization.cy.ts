describe("Whistleblower Navigate Home Page", () => {
  it("should see page properly internationalized", () => {

    cy.visit("#/?lang=en");

    cy.contains("div", "TEXT1_IT").should("not.exist");

    cy.contains("div", "TEXT2_IT").should("not.exist");

    cy.visit("#/?lang=de");

    cy.contains("div", "TEXT1_IT").should("exist");

    cy.contains("div", "TEXT2_IT").should("exist");
  });
});
