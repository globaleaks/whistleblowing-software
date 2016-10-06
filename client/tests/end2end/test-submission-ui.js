var utils = require('./utils.js');

describe('submission error elements', function() {

  it('submission should be blocked until recipients are selected', function() {
    browser.get('/#/submission');

    element(by.id('step-0-link')).click();

    element(by.id('step-0')).element(by.id('step-0-field-0-0-input-0')).sendKeys('err-panel test');
    var errPanel = by.id('SubmissionErrors');
    utils.waitUntilPresent(errPanel);

    var submitBtn = element(by.id('SubmitButton'));
    expect(submitBtn.isEnabled()).toEqual(false);

    // Navigation should take us back to the Recipient selection page
    element(by.css('#SubmissionErrors span.err-link')).click();

    element(by.id('step-receiver-selection')).element(by.id('receiver-0')).click();
    element(by.id('NextStepButton')).click();

    submitBtn = element(by.id('SubmitButton'));
    expect(submitBtn.isEnabled()).toEqual(true);
  });

});
