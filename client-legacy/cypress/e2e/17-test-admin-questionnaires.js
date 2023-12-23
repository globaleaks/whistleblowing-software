describe("admin add, configure and delete questionnaires", () => {
  const add_questionnaires = async (questionnaire_name) => {
    cy.get(".show-add-questionnaire-btn").click();
    cy.get("input[data-ng-model='new_questionnaire.name']").type(questionnaire_name);
    cy.get("#add-questionnaire-btn").click();
    cy.contains(questionnaire_name).should("be.visible");
  };

  const add_question = async (question_type) => {
    cy.get(".show-add-question-btn").first().click();
    cy.get("input[data-ng-model='new_field.label']").first().type(question_type);
    cy.get("select[data-ng-model='new_field.type']").first().select(question_type);
    cy.get("#add-field-btn").first().click();

    if (["Checkbox", "Selection box"].indexOf(question_type) === 0) {
      // Click on the element with text equal to `question_type` (second match)
      cy.contains(question_type).eq(0).click();

      // Loop to add 3 options
      for (let i = 0; i < 3; i++) {
        cy.get("[data-ng-click='addOption()']").click();
        cy.get("input[data-ng-model='option.label']").eq(i).type("option");
      }

      // Click on the button to delete the third option
      cy.get("[data-ng-click='delOption(option)']").eq(2).click();

      // Click on the first displayed element with the attribute data-ng-click="save_field(field)"
      cy.get("[data-ng-click='save_field(field)']").filter(':visible').first().click();
    }
  };

  const add_step = async (step_label) => {
    cy.get(".show-add-step-btn").click();
    cy.get("input[data-ng-model='new_step.label']").type(step_label);
    cy.get("#add-step-btn").click();
    cy.contains(step_label).should("be.visible");
  };

  it("should add and configure questionnaires", () => {
    cy.login_admin();
    cy.visit("/#/admin/questionnaires");

    add_questionnaires("Questionnaire 1");
    add_questionnaires("Questionnaire 2");

    cy.contains("Questionnaire 1").click();

    add_step("Step 1");
    add_step("Step 2");
    add_step("Step 3");

    // Open Step 2
    cy.contains("Step 2").click();

    const fieldTypes = Cypress.env("field_types");
    fieldTypes.forEach((questionType) => {
      add_question(questionType);
    });

    // Close Step 2
    cy.contains("Step 2").click();

    // Delete Step 3
    cy.get("[data-ng-click='delStep(step); $event.stopPropagation();']").eq(2).click();
    cy.get("#modal-action-ok").click();

    // Close Questionnaire 1
    cy.contains("Questionnaire 1").click();

    cy.get('[data-ng-show="questionnaire.editable"]:visible')
      .contains('Delete')
      .click({ multiple: true });
    cy.get("#modal-action-ok").click();

    cy.contains("a", "Question templates").click();

    fieldTypes.forEach((questionType) => {
      add_question(questionType);
    });

    cy.logout();
  });
});
