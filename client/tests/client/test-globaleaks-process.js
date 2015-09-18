describe('globaLeaks process', function() {
  var tip_text = 'topsecret';
  var receipts = [];
  var comment = 'comment';
  var comment_reply = 'comment reply';
  var receiver_username = "Receiver 1";
  var receiver_password = "ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#"

  var login_whistleblower = function(receipt) {
    var deferred = protractor.promise.defer();

    browser.get('/#/');
    element(by.model('formatted_keycode')).sendKeys(receipt).then(function() {
      element(by.css('[data-ng-click="view_tip(formatted_keycode)"]')).click().then(function() {
        expect(browser.getLocationAbsUrl()).toContain('/status');
        deferred.fulfill();
      });
    });

    return deferred;
  }

  var login_receiver = function(username, password) {
    var deferred = protractor.promise.defer();

    browser.get('/#/login');
    element(by.model('loginUsername')).element(by.xpath(".//*[text()='" + username + "']")).click().then(function() {
      element(by.model('loginPassword')).sendKeys(password).then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
          expect(browser.getLocationAbsUrl()).toContain('/receiver/tips');
          deferred.fulfill();
        });
      });
    });

    return deferred;
  }

  var perform_submission = function() {
    var deferred = protractor.promise.defer();

    browser.get('/#/submission');

    var remote = require('selenium-webdriver/remote');
    browser.setFileDetector(new remote.FileDetector());

    element(by.id('step-0')).element(by.id('receiver-0')).click().then(function () {
      element(by.id('NextStepButton')).click().then(function () {
        element(by.id('step-1')).element(by.id('field-0-input-0')).sendKeys(tip_text).then(function () {
          browser.executeScript('angular.element(document.querySelector(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
          element(by.id('step-1')).element(by.id('field-3')).element(by.xpath("//input[@type='file']")).sendKeys(__filename).then(function() {
            element(by.id('NextStepButton')).click().then(function () {
              element(by.id('step-2')).element(by.id('field-0-input-0')).click().then(function () {
                element(by.id('SubmitButton')).click().then(function() {
                  expect(browser.getLocationAbsUrl()).toContain('/receipt');
                  element(by.id('KeyCode')).getText().then(function (txt) {
                    receipts.unshift(txt);
                    deferred.fulfill();
                  });
                });
              });
            });
          });
        });
      });
    });

    return deferred;
  }

  it('should redirect to /submission by clicking on the blow the whistle button', function() {
    var deferred = protractor.promise.defer();

    browser.get('/#/');
    element(by.css('[data-ng-click="goToSubmission()"]')).click().then(function () {
      expect(browser.getLocationAbsUrl()).toContain('/submission');
      deferred.fulfill();
    });

    return deferred;
  });

  it('should be able to submit a tip (1)', function() {
    var deferred = protractor.promise.defer();

    perform_submission().then(function() {
      element(by.id('ReceiptButton')).click().then(function() {
        expect(browser.getLocationAbsUrl()).toContain('/status');
        deferred.fulfill();
      });
    });

    return deferred;
  });

  it('should be able to submit a tip (2)', function() {
    var deferred = protractor.promise.defer();

    perform_submission().then(function() {
      element(by.id('ReceiptButton')).click().then(function() {
        expect(browser.getLocationAbsUrl()).toContain('/status');
        deferred.fulfill();
      });
    });

    return deferred;
  });

  it('should be able to submit a tip (3)', function() {
    var deferred = protractor.promise.defer();

    perform_submission().then(function() {
      element(by.id('ReceiptButton')).click().then(function() {
        expect(browser.getLocationAbsUrl()).toContain('/status');
        deferred.fulfill();
      });
    });

    return deferred;
  });


  it('Whistleblower should be able to access the first submission', function() {
    var deferred = protractor.promise.defer();

    login_whistleblower(receipts[0]).then(function() {
      expect(element(by.xpath("//*[contains(text(),'" + tip_text + "')]")).getText()).toEqual(tip_text);
      deferred.fulfill();
    });

    return deferred;
  });

  it('Receiver should be able to access the first submission', function() {
    var deferred = protractor.promise.defer();

    login_receiver(receiver_username, receiver_password).then(function () {
      element(by.id('tip-0')).click().then(function() {
        expect(element(by.xpath("//*[contains(text(),'" + tip_text + "')]")).getText()).toEqual(tip_text);
        deferred.fulfill();
      });
    });

    return deferred;
  });

  it('Receiver should be able to leave a comment to the whistleblower', function() {
    var deferred = protractor.promise.defer();

    login_receiver(receiver_username, receiver_password).then(function () {
      element(by.id('tip-0')).click().then(function() {
        element(by.model('tip.newCommentContent')).sendKeys(comment);
        element(by.id('comment-action-send')).click().then(function() {
          element(by.id('comment-0')).element(by.css('.preformatted')).getText().then(function(c) {
            expect(c).toContain(comment);
            deferred.fulfill();
          });
        });
      });
    });

    return deferred;
  });

  it('Whistleblower should be able to read the comment from the receiver and reply', function() {
    var deferred = protractor.promise.defer();

    login_whistleblower(receipts[0]).then(function () {
      element(by.id('comment-0')).element(by.css('.preformatted')).getText().then(function(c) {
        expect(c).toEqual(comment);
        element(by.model('tip.newCommentContent')).sendKeys(comment_reply);
        element(by.id('comment-action-send')).click().then(function() {
          element(by.id('comment-0')).element(by.css('.preformatted')).getText().then(function(c) {
            expect(c).toContain(comment_reply);
            deferred.fulfill();
          });
        });
      });
    });

    return deferred;
  });

  it('Whistleblower should be able to attach a new file to the first submission', function() {
    var deferred = protractor.promise.defer();

    var remote = require('selenium-webdriver/remote');
    browser.setFileDetector(new remote.FileDetector());

    login_whistleblower(receipts[0]).then(function () {
      browser.executeScript('angular.element(document.querySelector(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
      element(by.xpath("//input[@type='file']")).sendKeys(__filename).then(function() {
        // TODO: test file addition
        deferred.fulfill();
      });
    });

    return deferred;
  });

  it('Receiver should be able to postpone first submission from tip page', function() {
    var deferred = protractor.promise.defer();

    login_receiver(receiver_username, receiver_password).then(function () {
      element(by.id('tip-0')).click().then(function() {
        element(by.id('tip-action-postpone')).click().then(function () {
          element(by.id('modal-action-ok')).click().then(function() {
            //TODO: check postpone
          deferred.fulfill();
          });
        });
      });
    });

    return deferred;
  });

  it('Receiver should be able to delete first submission from tip page', function() {
    var deferred = protractor.promise.defer();

    login_receiver(receiver_username, receiver_password).then(function () {
      element(by.id('tip-0')).click().then(function() {
        element(by.id('tip-action-delete')).click().then(function () {
          element(by.id('modal-action-ok')).click().then(function() {
            expect(browser.getLocationAbsUrl()).toContain('/receiver/tips');
            //TODO: check delete
            deferred.fulfill();
          });
        });
      });
    });

    return deferred;
  });

  it('Receiver should be able to postpone all tips (2 remaining out of 3)', function() {
    var deferred = protractor.promise.defer();

    login_receiver(receiver_username, receiver_password).then(function () {
      element(by.id('tip-action-select-all')).click().then(function() {
        element(by.id('tip-action-postpone-selected')).click().then(function () {
          element(by.id('modal-action-ok')).click().then(function() {
            expect(browser.getLocationAbsUrl()).toContain('/receiver/tips');
            //TODO: check postpone
            deferred.fulfill();
          });
        });
      });
    });

    return deferred;
  });

  it('Receiver should be able to delete all tips (2 remaining out of 3)', function() {
    var deferred = protractor.promise.defer();

    login_receiver(receiver_username, receiver_password).then(function () {
      element(by.id('tip-action-select-all')).click().then(function() {
        element(by.id('tip-action-delete-selected')).click().then(function () {
          element(by.id('modal-action-ok')).click().then(function() {
            expect(browser.getLocationAbsUrl()).toContain('/receiver/tips');
            //TODO: check delete
            deferred.fulfill();
          });
        });
      });
    });

    return deferred;
  });
});
