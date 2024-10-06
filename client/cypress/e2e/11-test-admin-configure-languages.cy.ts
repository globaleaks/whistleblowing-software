describe("admin configure languages", () => {
  it("should configure languages", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.get('[data-cy="languages"]').click();
    cy.get(".add-language-btn").click();

    if (Cypress.env('default_language')!=="en") {
      cy.get("body").click("top");
      cy.get('ng-select').last().click();
      cy.get('div.ng-option').contains('English [en]').click();
      cy.get('ul.selection-list li').should('contain', 'English [en]');
    }

    if (Cypress.env('default_language')!=="it") {
      cy.get("body").click("top");
      cy.get('ng-select').last().click();
      cy.get('div.ng-option').contains('Italian [it]').click();
      cy.get('ul.selection-list li').should('contain', 'Italian [it]');
    }

    if (Cypress.env('default_language')!=="de") {
      cy.get("body").click("top");
      cy.get('ng-select').last().click();
      cy.get('div.ng-option').contains('German [de]').click();
      cy.get('ul.selection-list li').should('contain', 'German [de]');
    }

    cy.get("#save_language").click();
    cy.waitForUrl("/#/admin/settings");
    cy.get('[data-cy="languages"]').click();

    if (Cypress.env('default_language')=="it") {
      cy.get(".non-default-language").eq(0).click();
    }

    cy.get("#save_language").click();
    cy.get('[data-cy="languages"]').click();

    if (Cypress.env('default_language')=="en") {
      cy.get(".remove-lang-btn").eq(1).click();
    } else {
      cy.get(".remove-lang-btn").eq(2).click();
    }

    cy.get("#save_language").should('exist').should('be.visible').click();

    cy.waitForUrl("/#/admin/settings");
    cy.get('#LanguagePickerBox').should('be.visible', { timeout: 10000 }).find('ng-select').last().click().get('ng-dropdown-panel').contains('Deutsch').click();

    cy.get('[name="node.dataModel.header_title_homepage"]').clear().type("TEXT1_IT");
    cy.get('[name="node.dataModel.presentation"]').clear().type("TEXT2_IT");
    cy.get('button.btn.btn-primary').eq(0).get("#save_settings").click();

    cy.get('#language-picker-select').click();
    cy.get(`[data-cy="${Cypress.env('default_language')}"]`).trigger('click');

    cy.visit("/#/admin/settings");
    cy.get('[data-cy="languages"]').click();
    if (Cypress.env('default_language')=="it") {
      cy.get(".non-default-language").eq(0).click();
    }
    cy.get("#save_language").click();

    cy.logout();
  });
});
