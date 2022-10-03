describe("admin add, configure and delete questionnaires", function() {
  var add_questionnaires = async function(questionnaire_name) {
    await element(by.css(".show-add-questionnaire-btn")).click();
    await element(by.model("new_questionnaire.name")).sendKeys(questionnaire_name);
    await element(by.id("add-questionnaire-btn")).click();
    await browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + questionnaire_name + "']"));
  };

  var add_question = async function(question_type) {
    await element.all(by.css(".show-add-question-btn")).first().click();
    await element.all(by.model("new_field.label")).first().sendKeys(question_type);
    await element.all(by.model("new_field.type")).first().element(by.xpath(".//*[text()='" + question_type + "']")).click();
    await element.all(by.id("add-field-btn")).first().click();

    if(["Checkbox", "Selection box"].indexOf(question_type) === 0) {
      await element.all(by.xpath(".//*[text()='" + question_type + "']")).get(1).click();

      for (var i=0; i<3; i++) {
        await element(by.css("[data-ng-click=\"addOption()\"]")).click();
        await element.all(by.model("option.label")).get(i).sendKeys("option");
      }

      await element.all(by.css("[data-ng-click=\"delOption(option)\"]")).get(2).click();

      await browser.gl.utils.clickFirstDisplayed(by.css("[data-ng-click=\"save_field(field)\"]"));
    }
  };

  var add_step = async function(step_label) {
    await element(by.css(".show-add-step-btn")).click();
    await element(by.model("new_step.label")).sendKeys(step_label);
    await element(by.id("add-step-btn")).click();
    await browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + step_label + "']"));
  };

  it("should add new questionnaires", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/questionnaires");

    await add_questionnaires("Questionnaire 1");
    await add_questionnaires("Questionnaire 2");
  });

  it("should configure steps and questions", async function() {
    // Open Questionnaire 1
    await element(by.xpath(".//*[text()='Questionnaire 1']")).click();

    await add_step("Step 2");
    await add_step("Step 3");

    // Open Step 1
    await element(by.xpath(".//*[text()='Step 2']")).click();

    for(var i=0; i<browser.gl.utils.vars.field_types.length; i++){
      await add_question(browser.gl.utils.vars.field_types[i]);
    }

    // Close Step 1
    await element(by.xpath(".//*[text()='Step 2']")).click();

    // Delete Step 3
    await element.all(by.css("[data-ng-click=\"delStep(step); $event.stopPropagation();\"]")).get(2).click();

    await element(by.id("modal-action-ok")).click();

    // Close Questionnaire 1
    await element(by.xpath(".//*[text()='Questionnaire 1']")).click();
  });

  it("should del existing questionnaires", async function() {
    await element.all(by.cssContainingText("button", "Delete")).last().click();
    await element(by.id("modal-action-ok")).click();
  });

  it("should add new question templates", async function() {
    await element(by.cssContainingText("a", "Question templates")).click();

    for(var i=0; i<browser.gl.utils.vars.field_types.length; i++){
      await add_question(browser.gl.utils.vars.field_types[i]);
    }

    await browser.gl.utils.logout();
  });
});
