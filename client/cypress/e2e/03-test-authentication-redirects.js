describe("perform redirects on authenticated pages", function () {
  it("test redirect to login page using /login url", function () {
    cy.visit("/#/login");
  });

  it("test redirect to login page using /admin url", function () {
    cy.visit("/#/admin");
  });

  it("test rtip redirect to login page", function () {
    cy.visit("/#/status/2f0535eb-9710-47e5-8082-5f882d4ec770");
  });

  it("test admin redirect to login page", function () {
    cy.visit("/#/admin/settings");
  });
});
