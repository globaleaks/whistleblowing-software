var utils = require('./utils.js');

var fs = require('fs');
var path = require('path');

var fileToUpload = path.resolve(__filename);

describe('globaLeaks process', function() {
  var tip_text = 'topsecret';
  var receipts = [];
  var comment = 'comment';
  var comment_reply = 'comment reply';
  var receiver_username = "Recipient 1";
  var receiver_password = "ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#"

  var login_whistleblower = function(receipt) {
    return protractor.promise.controlFlow().execute(function() {
      var deferred = protractor.promise.defer();

      browser.get('/#/');

      element(by.model('formatted_keycode')).sendKeys(receipt).then(function() {
        element(by.css('[data-ng-click="view_tip(formatted_keycode)"]')).click().then(function() {
          utils.waitForUrl('/status');
          deferred.fulfill();
        });
      });

      return deferred.promise;
    });
  }

  var login_receiver = function(username, password) {
    return protractor.promise.controlFlow().execute(function() {
      var deferred = protractor.promise.defer();

      browser.get('/#/login');

      element(by.model('loginUsername')).element(by.xpath(".//*[text()='" + username + "']")).click().then(function() {
        element(by.model('loginPassword')).sendKeys(password).then(function() {
          element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
            utils.waitForUrl('/receiver/tips');
            deferred.fulfill();
          });
        });
      });

      return deferred.promise;
    });
  }

  var perform_submission = function(done) {
    browser.get('/#/submission');

    element(by.id('step-0')).element(by.id('receiver-0')).click().then(function () {
      element(by.id('NextStepButton')).click().then(function () {
        element(by.id('step-1')).element(by.id('step-1-field-0-0-input-0')).sendKeys(tip_text).then(function () {
          if (utils.testFileUpload()) {
            browser.executeScript('angular.element(document.querySelector(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
            element(by.id('step-1')).element(by.id('step-1-field-3-0')).element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload).then(function() {
              element(by.id('step-1')).element(by.id('step-1-field-3-0')).element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload).then(function() {
                element(by.id('NextStepButton')).click().then(function () {
                  element(by.id('step-2')).element(by.id('step-2-field-0-0-input-0')).click().then(function () {
                    var submit_button = element(by.id('SubmitButton'));
                    var isClickable = protractor.ExpectedConditions.elementToBeClickable(submit_button);
                    browser.wait(isClickable);
                    submit_button.click().then(function() {
                      utils.waitForUrl('/receipt');
                      element(by.id('KeyCode')).getText().then(function (txt) {
                        receipts.unshift(txt);
                      });
                    });
                  });
                });
              });
            });
          } else {
            element(by.id('NextStepButton')).click().then(function () {
              element(by.id('step-2')).element(by.id('step-2-field-0-0-input-0')).click().then(function () {
                var submit_button = element(by.id('SubmitButton'));
                var isClickable = protractor.ExpectedConditions.elementToBeClickable(submit_button);
                browser.wait(isClickable);
                submit_button.click().then(function() {
                  utils.waitForUrl('/receipt');
                  element(by.id('KeyCode')).getText().then(function (txt) {
                    receipts.unshift(txt);
                  });
                });
              });
            });
          }

          element(by.id('ReceiptButton')).click().then(function() {
            utils.waitForUrl('/status');
            element(by.id('LogoutLink')).click().then(function() {
              utils.waitForUrl('/');
              done();
            });
          });
        });
      });
    });
  }

  it('should redirect to /submission by clicking on the blow the whistle button', function(done) {
    browser.get('/#/');
    element(by.css('[data-ng-click="goToSubmission()"]')).click().then(function () {
      utils.waitForUrl('/submission');
      done();
    });
  });

  it('Whistleblowers should be able to submit tips (1)', function(done) {
    perform_submission(done);
  });

  it('Whistleblowers should be able to submit tips (2)', function(done) {
    perform_submission(done);
  });

  it('Whistleblowers should be able to submit tips (3)', function(done) {
    perform_submission(done);
  });

  it('Whistleblower should be able to access the first submission', function(done) {
    login_whistleblower(receipts[0]).then(function() {
      expect(element(by.xpath("//*[contains(text(),'" + tip_text + "')]")).getText()).toEqual(tip_text);
      element(by.id('LogoutLink')).click().then(function() {
        utils.waitForUrl('/');
        done();
      });
    });
  });

  it('Recipient should be able to access the first submission', function(done) {
    login_receiver(receiver_username, receiver_password).then(function() {
      element(by.id('tip-0')).click().then(function() {
        expect(element(by.xpath("//*[contains(text(),'" + tip_text + "')]")).getText()).toEqual(tip_text);
        done();
      });
    });
  });

  it('Recipient should be able to refresh tip page', function(done) {
    element(by.id('link-reload')).click().then(function () {
      browser.waitForAngular();
      done();
    });
  });

  it('Recipient should be able to see files and download them', function(done) {
    if (utils.testFileUpload()) {
      expect(element.all(by.cssContainingText("button", "download")).count()).toEqual(2);
      if (utils.testFileDownload()) {
        element.all(by.cssContainingText("button", "download")).get(0).click().then(function() {
          browser.waitForAngular();
          done();
        });
      } else {
        done();
      }
    }
  });

  it('Recipient should be able to leave a comment to the whistleblower', function(done) {
    login_receiver(receiver_username, receiver_password).then(function() {
      element(by.id('tip-0')).click().then(function() {
        element(by.model('tip.newCommentContent')).sendKeys(comment);
        element(by.id('comment-action-send')).click().then(function() {
          element(by.id('comment-0')).element(by.css('.preformatted')).getText().then(function(c) {
            expect(c).toContain(comment);
            element(by.id('LogoutLink')).click().then(function() {
              utils.waitForUrl('/login');
              done();
            });
          });
        });
      });
    });
  });

  it('Whistleblower should be able to read the comment from the receiver and reply', function(done) {
    login_whistleblower(receipts[0]).then(function() {
      element(by.id('comment-0')).element(by.css('.preformatted')).getText().then(function(c) {
        expect(c).toEqual(comment);
        element(by.model('tip.newCommentContent')).sendKeys(comment_reply);
        element(by.id('comment-action-send')).click().then(function() {
          element(by.id('comment-0')).element(by.css('.preformatted')).getText().then(function(c) {
            expect(c).toContain(comment_reply);
            done();
          });
        });
      });
    });
  });

  it('Whistleblower should be able to attach a new file to the first submission', function(done) {
    login_whistleblower(receipts[0]).then(function() {
      if (utils.testFileUpload()) {
        browser.executeScript('angular.element(document.querySelector(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
        element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload).then(function() {
          element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload).then(function() {
            // TODO: test file addition
            element(by.id('LogoutLink')).click().then(function() {
              utils.waitForUrl('/');
              done();
            });
          });
        });
      }
    });
  });

  it('Recipient should be able to export the submission', function(done) {
    login_receiver(receiver_username, receiver_password).then(function() {
      element(by.id('tip-0')).click().then(function() {
        if (utils.testFileDownload()) {
          element(by.id('tip-action-export')).click().then(function () {
            browser.waitForAngular();
            // TODO: test the downloaded zip file opening it and verifying its content.
            done();
          });
        } else {
          done();
        }
      });
    });
  });

  it('Recipient should be able to postpone first submission from tip page', function(done) {
    login_receiver(receiver_username, receiver_password).then(function() {
      element(by.id('tip-0')).click().then(function() {
        element(by.id('tip-action-postpone')).click().then(function () {
          element(by.id('modal-action-ok')).click().then(function() {
            //TODO: check postpone
            element(by.id('LogoutLink')).click().then(function() {
              utils.waitForUrl('/login');
              done();
            });
          });
        });
      });
    });
  });

  it('Recipient should be able to delete first submission from tip page', function(done) {
    login_receiver(receiver_username, receiver_password).then(function() {
      element(by.id('tip-0')).click().then(function() {
        element(by.id('tip-action-delete')).click().then(function () {
          element(by.id('modal-action-ok')).click().then(function() {
            utils.waitForUrl('/receiver/tips');
            //TODO: check delete
            element(by.id('LogoutLink')).click().then(function() {
              utils.waitForUrl('/login');
              done();
            });
          });
        });
      });
    });
  });

  it('Recipient should be able to postpone all tips', function(done) {
    login_receiver(receiver_username, receiver_password).then(function() {
      element(by.id('tip-action-select-all')).click().then(function() {
        element(by.id('tip-action-postpone-selected')).click().then(function () {
          element(by.id('modal-action-ok')).click().then(function() {
            utils.waitForUrl('/receiver/tips');
            //TODO: check postpone
            element(by.id('LogoutLink')).click().then(function() {
              utils.waitForUrl('/login');
              done();
            });
          });
        });
      });
    });
  });
});
