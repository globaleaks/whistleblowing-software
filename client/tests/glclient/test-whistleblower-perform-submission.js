describe('globaLeaks wb submission', function() {
  var tip_text = 'test submission 1';
  var receipt = '';

  it('should redirect to /submission by clicking on the blow the whisle button', function() {
    browser.get('/#/');
    element(by.css('[data-ng-click="goToSubmission()"]')).click().then(function () {
      expect(browser.getLocationAbsUrl()).toContain('/#/submission');
    });
  });

  it('should be able to submit a tip', function() {
    browser.get('/#/submission');

    element(by.id('step-0')).element(by.id('receiver-0')).click().then(function () {
      element(by.id('NextStepButton')).click().then(function () {
        element(by.tagName('textarea')).sendKeys(tip_text).then(function () {
          browser.executeScript('$(\'input[type="file"]\').attr("style", "opacity:0; position:absolute;");');
          element(by.id('step-1')).element(by.id('field-3-input')).element(by.xpath("//input[@type='file']")).sendKeys(__filename).then(function() {
            element(by.id('NextStepButton')).click().then(function () {
              element(by.id('step-2')).element(by.id('field-0-input')).click();
              element(by.id('SubmitButton')).click().then(function() {
                expect(browser.getLocationAbsUrl()).toContain('/#/receipt');
                element(by.id('KeyCode')).getText().then(function (txt) {
                  receipt = txt;
                });
              });
            });
          });
        });
      });
    });
  });

  it('should be able to access the submission', function() {
    browser.get('/#/');
    element(by.model('formatted_keycode')).sendKeys( receipt );
    element(by.css('[data-ng-click="view_tip(formatted_keycode)"]')).click().then(function () {
      expect(element( by.xpath("//*[contains(text(),'" + tip_text + "')]") ).getText()).toEqual(tip_text);
    });
  });

});
