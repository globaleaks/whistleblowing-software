var utils = require('./utils.js');

describe('admin add, configure and delete questionnaires', function() {
  var add_questionnaires = function(questionnaire_name) {
    element(by.model('new_questionnaire.name')).sendKeys(questionnaire_name);
    element(by.id('add-questionnaire-button')).click();
    utils.waitUntilReady(element(by.xpath(".//*[text()='" + questionnaire_name + "']")));
  };

  var add_question = function(question_type) {
    element.all(by.model('new_field.label')).first().sendKeys(question_type);
    element.all(by.model('new_field.type')).first().element(by.xpath(".//*[text()='" + question_type + "']")).click();
    element.all(by.id('add-field-button')).first().click();
  };

  var add_step = function(step_label) {
    element(by.model('new_step.label')).sendKeys(step_label);
    element(by.id('add-step-button')).click();
    utils.waitUntilReady(element(by.xpath(".//*[text()='" + step_label + "']")));
  };

  it('should add new questionnaires', function() {
    browser.setLocation('admin/questionnaires');

    utils.waitUntilReady(element(by.xpath(".//*[text()='Default']")));

    add_questionnaires('Questionnaire 1');
    add_questionnaires('Questionnaire 2');
  });

  it('should configure steps and questions', function() {
    // Open Questionnaire 1
    element(by.xpath(".//*[text()='Questionnaire 1']")).click();

    add_step("Step 1");
    add_step("Step 2");

    // Open Step 1
    element(by.xpath(".//*[text()='Step 1']")).click();

    for(var i=0; i<utils.vars.field_types.length; i++){
      add_question(utils.vars.field_types[i]);
    }

    // Close Step 1
    element(by.xpath(".//*[text()='Step 1']")).click();

    // Close Questionnaire 1
    element(by.xpath(".//*[text()='Questionnaire 1']")).click();
  });

  it('should del existing questionnaires', function() {
    element.all(by.css('.actionButtonDelete')).last().click();
  });

  it('should add new question templates', function() {
    element(by.cssContainingText("a", "Question templates")).click();

    element(by.cssContainingText("span", "Do you want to provide your identification information?")).click();

    for(var i=0; i<utils.vars.field_types.length; i++){
      add_question(utils.vars.field_types[i]);
    }
  });
});
