var utils = require('./utils.js');

exports.receiver = function() {
  this.viewMostRecentSubmission = function() {
    return element(by.id('tip-0')).click();
  };

  this.addPublicKey = function(pub_pgp_key) {
    browser.setLocation('receiver/preferences');
    element(by.cssContainingText("a", "Encryption settings")).click();
    var pgpTxtArea = element(by.model('preferences.pgp_key_public'));

    return pgpTxtArea.isDisplayed().then(function(displayed) {
      if (!displayed) {
        clickDelPubKey();
      }

    pgpTxtArea.clear();
    pgpTxtArea.sendKeys(pub_pgp_key);
    return element(by.cssContainingText("span", "Update notification and encryption settings")).click();
    });
  };

  function clickDelPubKey() {
    element(by.model('preferences.pgp_key_remove')).click();
    return element(by.cssContainingText("span", "Update notification and encryption settings")).click();
  }

  this.removePublicKey = function() {
    browser.setLocation('receiver/preferences');
    element(by.cssContainingText('a', 'Encryption settings')).click();
    return clickDelPubKey();
  };
};

exports.whistleblower = function() {
  this.performSubmission = function(title) {
    browser.get('/#/submission');

    browser.wait(function(){
      // Wait until the proof of work is resolved;
      return element(by.id('submissionForm')).evaluate('submission').then(function(submission) {
        return submission.pow === true;
      });
    }, utils.browserTimeout());

    element(by.id('step-receiver-selection')).element(by.id('receiver-0')).click();
    element(by.id('step-receiver-selection')).element(by.id('receiver-1')).click();
    element(by.id('NextStepButton')).click();
    element(by.id('step-0')).element(by.id('step-0-field-0-0-input-0')).sendKeys(title);

    var submit_button = element(by.id('SubmitButton'));
    var isClickable = protractor.ExpectedConditions.elementToBeClickable(submit_button);
    browser.wait(isClickable);
    submit_button.click();
    utils.waitForUrl('/receipt');
    return element(by.id('KeyCode')).getText();
  };

  this.viewReceipt = function(receipt) {
    browser.get('/#/');

    return element(by.model('formatted_keycode')).sendKeys(receipt).then(function() {
      element(by.id('ReceiptButton')).click().then(function() {
        utils.waitForUrl('/status');
      });
    });

  };

  this.submitFile = function(fname) {
    browser.executeScript('angular.element(document.querySelector(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    return element(by.xpath("//input[@type='file']")).sendKeys(fname).then(function() {
      return browser.waitForAngular();
    });
  };
};
