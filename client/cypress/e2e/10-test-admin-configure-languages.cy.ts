describe("admin configure languages", () => {
  it("should configure languages", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("button", "Languages").click();
    cy.get(".add-language-btn").click();

    cy.get("body").click("top");
    cy.get('ng-select').last().click();
    cy.get('div.ng-option').contains('English [en]').click();
    cy.get('ul.selection-list li').should('contain', 'English [en]');

    cy.get("body").click("top");
    cy.get('ng-select').last().click();
    cy.get('div.ng-option').contains('Italian [it]').click();
    cy.get('ul.selection-list li').should('contain', 'Italian [it]');

    cy.get("body").click("top");
    cy.get('ng-select').last().click();
    cy.get('div.ng-option').contains('German [de]').click();
    cy.get('ul.selection-list li').should('contain', 'German [de]');

    cy.contains("button", "Save").click();
    cy.visit("/#/admin/settings");
    cy.contains("button", "Languages").click();

    cy.get(".non-default-language").eq(1).click();
    cy.contains("button", "Save").click();
    cy.contains("button", "Sprachen").click();

    cy.get(".remove-lang-btn").eq(1).click();
    cy.contains("button", "Speichern").click();
    cy.waitForLoader()

    cy.visit("/#/admin/settings");
    cy.get('#language-picker-box').find('ng-select').last().click().get('ng-dropdown-panel').contains('Deutsch').click();

    cy.get('[name="node.dataModel.header_title_homepage"]').clear().type("TEXT1_IT");
    cy.get('[name="node.dataModel.presentation"]').clear().type("TEXT2_IT");
    cy.get('button.btn.btn-primary').eq(0).contains('Speichern').click();

    cy.get('#language-picker-box').find('ng-select').last().click().get('ng-dropdown-panel').contains('English').click();
    cy.visit("/#/admin/settings");
    cy.contains("button", "Languages").click();
    cy.get(".non-default-language").eq(0).click();
    cy.contains("button", "Save").click();

    cy.logout();
  });
});
