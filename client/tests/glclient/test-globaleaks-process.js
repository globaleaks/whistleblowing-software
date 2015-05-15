describe('globaLeaks process', function() {
  var tip_text = 'topsecret';
  var receipt = '';
  var private_message = 'priv8 message';
  var private_message_reply = 'priv8 message reply';
  var receiver_username = "Receiver 1";
  var receiver_password = "ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#"

  var login_whistleblower = function(receipt) {
    var deferred = protractor.promise.defer();

    browser.get('/#/');
    element(by.model('formatted_keycode')).sendKeys(receipt).then(function() {
      element(by.css('[data-ng-click="view_tip(formatted_keycode)"]')).click().then(function() {
        expect(browser.getLocationAbsUrl()).toContain('/#/status');
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
          expect(browser.getLocationAbsUrl()).toContain('/#/receiver/tips');
          deferred.fulfill();
        });
      });
    });

    return deferred;
  }

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
        element(by.id('step-1')).element(by.id('field-0-input')).sendKeys(tip_text).then(function () {
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

  it('Whistleblower should be able to access the submission', function() {
    login_whistleblower(receipt).then(function() {
      expect(element(by.xpath("//*[contains(text(),'" + tip_text + "')]")).getText()).toEqual(tip_text);
    });
  });

  it('Receiver should be able to access the submission', function() {
    login_receiver(receiver_username, receiver_password).then(function () {
      element(by.id('tip-0')).element(by.css('.tip-action-open')).click().then(function() {
        expect(element(by.xpath("//*[contains(text(),'" + tip_text + "')]")).getText()).toEqual(tip_text);
      });
    });
  });

  it('Receiver should be able to send a private message to the whistleblower', function() {
    login_receiver(receiver_username, receiver_password).then(function () {
      element(by.id('tip-0')).element(by.css('.tip-action-open')).click().then(function() {
        element(by.model('tip.newMessageContent')).sendKeys(private_message);
        element(by.id('message-action-send')).click().then(function() {
          element(by.id('message-0')).element(by.css('.preformatted')).getText().then(function(message) {
            expect(message).toContain(private_message);
          });
        });
      });
    });
  });

  it('Whistleblower should be able to read the private message from the receiver and reply', function() {
    login_whistleblower(receipt).then(function () {
      element(by.id('message-0')).element(by.css('.preformatted')).getText().then(function(message) {
        expect(message).toEqual(private_message);
        element(by.model('tip.newMessageContent')).sendKeys(private_message_reply);
        element(by.css('[data-ng-click="newMessage()"]')).click().then(function() {
          element(by.id('message-1')).element(by.css('.preformatted')).getText().then(function(message) {
            expect(message).toContain(private_message);
          });
        });
      });
    });
  });

  it('Whistleblower should be able to attach a new file to the tip', function() {
    login_whistleblower(receipt).then(function () {
      browser.executeScript('$(\'input[type="file"]\').attr("style", "opacity:0; position:absolute;");');
      element(by.xpath("//input[@type='file']")).sendKeys(__filename).then(function() {
        // TODO: test file addition
      });
    });
  });

  it('Receiver should be able to postpone a tip', function() {
    login_receiver(receiver_username, receiver_password).then(function () {
      element(by.id('tip-0')).element(by.css('.tip-action-open')).click().then(function() {
        element(by.css('.tip-action-postpone')).click().then(function () {
          element(by.css('.modal-action-ok')).click().then(function() {
            //TODO: check postpone
          });
        });
      });
    });
  });

  it('Receiver should be able to delete a tip', function() {
    login_receiver(receiver_username, receiver_password).then(function () {
      element(by.id('tip-0')).element(by.css('.tip-action-open')).click().then(function() {
        element(by.css('.tip-action-delete')).click().then(function () {
          element(by.css('.modal-action-ok')).click().then(function() {
            expect(browser.getLocationAbsUrl()).toContain('/#/receiver/tips');
            //TODO: check delete
          });
        });
      });
    });
  });

});
