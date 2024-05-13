describe("configure simple login", () => {
    it("should configure simple login", function () {
        cy.login_admin();
        cy.waitForUrl("/#/admin/home");
        cy.visit("/#/admin/settings");
        cy.get('[data-cy="advanced"]').click().should("be.visible", { timeout: 10000 }).click();
        cy.get('input[name="node.dataModel.simplified_login"]').click();
        cy.get("#save").click();
        cy.logout();

        cy.simple_login_receiver();
        cy.logout();

        cy.simple_login_admin();

        cy.get("#admin_settings").click();
        cy.get('[data-cy="advanced"]').click().should("be.visible", { timeout: 10000 }).click();
        cy.get('input[name="node.dataModel.simplified_login"]').click();
        cy.get("#save").click();
        cy.logout();
    });
});