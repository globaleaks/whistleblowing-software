describe("admin configure languages", () => {
  it("should configure languages", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.contains("a", "Languages").click();

    cy.get(".add-language-btn").click();

    cy.get('div.col-md-12[data-ng-if="showLangSelect"] .ui-select-toggle').click();
    cy.get('ul.ui-select-choices-content li')
    .contains('English [en]')
    .should(($element) => {
      if ($element.length > 0) {
        $element.click();
      }
    });

    cy.get("body").click("top");
    cy.get('div.col-md-12[data-ng-if="showLangSelect"] .ui-select-toggle').click();
    cy.get('ul.ui-select-choices-content li')
    .contains('Italian [it]')
    .should(($element) => {
      if ($element.length > 0) {
        $element.click();
      }
    });

    cy.get("body").click("top");
    cy.get('div.col-md-12[data-ng-if="showLangSelect"] .ui-select-toggle').click();
    cy.get('ul.ui-select-choices-content li').contains('German [de]').click();

    cy.get('button.btn.btn-primary').eq(2).contains('Save').click();

    cy.contains("label", "Logo").should("be.visible");

    cy.visit("/#/admin/settings");
    cy.contains("a", "Languages").click();

    cy.get(".non-default-language").eq(0).click();
    cy.get('button.btn.btn-primary').eq(2).contains('Save').click();

    cy.contains("label", "Logo").should("be.visible");
    cy.contains("a", "Languages").click();

    cy.get(".non-default-language").eq(0).click();
    cy.get(".remove-lang-btn").eq(0).click();
    cy.get('button.btn.btn-primary').eq(2).contains('Save').click();

    cy.contains("label", "Logo").should("be.visible");

    cy.contains("a", "Languages").click();
    cy.get('button.btn.btn-primary').eq(2).contains('Save').click();

    cy.contains("label", "Logo").should("be.visible");

    cy.contains("a", "Languages").click();

    cy.get('#LanguagePickerBox select').select('Italiano');

    cy.contains("label", "Logo").should("be.visible");

    cy.get('[data-ng-model="resources.node.header_title_homepage"]').clear().type("TEXT1_IT");
    cy.get('[data-ng-model="resources.node.presentation"]').clear().type("TEXT2_IT");
    cy.get('button.btn.btn-primary').eq(0).contains('Salva').click();

    cy.contains("label", "Logo").should("be.visible");

    cy.get('#LanguagePickerBox select').select('English');

    cy.logout();
  });
});
