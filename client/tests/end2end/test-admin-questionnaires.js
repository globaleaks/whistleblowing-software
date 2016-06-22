var utils = require('./utils.js');

describe('admin add, configure and delete questionnaires', function() {
  var add_questionnaires = function(questionnaire_name) {
    var add_button = element(by.css('[data-ng-click="add_questionnaire()"]'));
    element(by.model('new_questionnaire.name')).sendKeys(questionnaire_name);
    browser.actions().mouseMove(add_button).click().perform();
    utils.waitUntilReady(element(by.xpath(".//*[text()='" + questionnaire_name + "']")));
  };

  var add_question = function(question_type) {
    var add_button = element.all(by.css('[data-ng-click="add_field()"]')).first();
    element.all(by.model('new_field.label')).first().sendKeys(question_type);
    element.all(by.model('new_field.type')).first().element(by.xpath(".//*[text()='" + question_type + "']")).click();
    browser.actions().mouseMove(add_button).click().perform();
  };

  var add_step = function(step_label) {
    var add_button = element(by.css('[data-ng-click="add_step()"]'));
    element(by.model('new_step.label')).sendKeys(step_label);
    browser.actions().mouseMove(add_button).click().perform();
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
