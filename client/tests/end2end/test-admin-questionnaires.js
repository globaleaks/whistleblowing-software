describe('admin add, configure and delete questionnaires', function() {
  var add_questionnaires = function(questionnaire_name) {
    element(by.css('.show-add-questionnaire-btn')).click();
    element(by.model('new_questionnaire.name')).sendKeys(questionnaire_name);
    element(by.id('add-questionnaire-btn')).click();
    browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + questionnaire_name + "']"));
  };

  var add_question = function(question_type) {
    element.all(by.css('.show-add-question-btn')).first().click();
    element.all(by.model('new_field.label')).first().sendKeys(question_type);
    element.all(by.model('new_field.type')).first().element(by.xpath(".//*[text()='" + question_type + "']")).click();
    element.all(by.id('add-field-btn')).first().click();

    if(['Checkbox', 'Multiple choice input', 'Selection box'].indexOf(question_type) === 0) {
      element.all(by.xpath(".//*[text()='" + question_type + "']")).get(1).click();

      for (var i=0; i<3; i++) {
        element(by.css('[data-ng-click="addOption()"]')).click();
        element.all(by.model('option.label')).get(i).sendKeys('option');
      }

      element.all(by.css('[data-ng-click="delOption(option)"]')).get(2).click();

      browser.gl.utils.clickFirstDisplayed(by.css('[data-ng-click="save_field(field)"]'));
    }
  };

  var add_step = function(step_label) {
    element(by.css('.show-add-step-btn')).click();
    element(by.model('new_step.label')).sendKeys(step_label);
    element(by.id('add-step-btn')).click();
    browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + step_label + "']"));
  };

  it('should add new questionnaires', function() {
    browser.setLocation('admin/questionnaires');

    browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='Default']"));

    add_questionnaires('Questionnaire 1');
    add_questionnaires('Questionnaire 2');
  });

  it('should configure steps and questions', function() {
    // Open Questionnaire 1
    element(by.xpath(".//*[text()='Questionnaire 1']")).click();

    add_step("Step 1");
    add_step("Step 2");
    add_step("Step 3");

    // Open Step 1
    element(by.xpath(".//*[text()='Step 1']")).click();

    for(var i=0; i<browser.gl.utils.vars.field_types.length; i++){
      add_question(browser.gl.utils.vars.field_types[i]);
    }

    // Close Step 1
    element(by.xpath(".//*[text()='Step 1']")).click();

    // Delete Step 3
    element.all(by.css('[data-ng-click="delStep(step); $event.stopPropagation();"]')).get(2).click();

    // Close Questionnaire 1
    element(by.xpath(".//*[text()='Questionnaire 1']")).click();
  });

  it('should del existing questionnaires', function() {
    element.all(by.cssContainingText("button", "Delete")).last().click();
  });

  it('should add new question templates', function() {
    element(by.cssContainingText("a", "Question templates")).click();

    element(by.cssContainingText("span", "Do you want to provide your identification information?")).click();

    for(var i=0; i<browser.gl.utils.vars.field_types.length; i++){
      add_question(browser.gl.utils.vars.field_types[i]);
    }
  });
});
