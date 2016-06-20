var utils = require('./utils.js');

describe('admin add, configure and delete questionnaires', function() {
  it('should add new questionnaires', function() {
    browser.setLocation('admin/questionnaires');

    utils.waitUntilReady(element(by.xpath(".//*[text()='Default']")));

    var add_questionnaires = function(questionnaire_name) {
      element(by.model('new_questionnaire.name')).sendKeys(questionnaire_name);
      element(by.css('[data-ng-click="add_questionnaire()"]')).click();
      utils.waitUntilReady(element(by.xpath(".//*[text()='" + questionnaire_name + "']")));
    };

    add_questionnaires('Questionnaire 1');
    add_questionnaires('Questionnaire 2');
    // TODO check if the questionnaires were made
  });

  it('should del existing questionnaires', function() {
    element.all((by.css('.actionButtonDelete'))).last().click();
  });
});
