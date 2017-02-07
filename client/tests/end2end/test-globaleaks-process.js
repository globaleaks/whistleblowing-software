var utils = require('./utils.js');

var path = require('path');

var fileToUpload = path.resolve(__filename);

describe('globaLeaks process', function() {
  var tip_text = 'topsecret';
  var receipts = [];
  var comment = 'comment';
  var comment_reply = 'comment reply';
  var message = 'message';
  var message_reply = 'message reply';
  var receiver_username = "Recipient1";
  var receiver_password = utils.vars['user_password'];

  var perform_submission = function() {
    browser.get('/#/');
    element(by.cssContainingText("button", "Blow the whistle")).click();
    utils.waitUntilPresent(by.cssContainingText("div.modal-title", "Warning! You are not anonymous."));
    element(by.id("answer-2")).click();
    element(by.cssContainingText("a", "Proceed to submission")).click();

    utils.waitUntilPresent(by.id('submissionForm'));

    browser.wait(function(){
      // Wait until the proof of work is resolved;
      return element(by.id('submissionForm')).evaluate('submission').then(function(submission) {
        return submission.pow === true;
      });
    });

    element(by.id('step-receiver-selection')).element(by.id('receiver-0')).click();

    element(by.id('NextStepButton')).click();

    element(by.id('PreviousStepButton')).click();

    element(by.id('step-receiver-selection')).element(by.id('receiver-1')).click();

    element(by.id('NextStepButton')).click();

    element(by.id('step-0')).element(by.id('step-0-field-0-0-input-0')).sendKeys(tip_text);
    if (utils.testFileUpload()) {
      browser.executeScript('angular.element(document.querySelector(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
      element(by.id('step-0')).element(by.id('step-0-field-2-0')).element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload).then(function() {
        browser.waitForAngular();
        element(by.id('step-0')).element(by.id('step-0-field-2-0')).element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload).then(function() {
          browser.waitForAngular();
        });
      });
    }

    var submit_button = element(by.id('SubmitButton'));
    var isClickable = protractor.ExpectedConditions.elementToBeClickable(submit_button);
    browser.wait(isClickable);

    submit_button.click().then(function() {
      utils.waitForUrl('/receipt');
      element(by.id('KeyCode')).getText().then(function (txt) {
        receipts.unshift(txt);
        element(by.id('ReceiptButton')).click().then(function() {
          utils.waitForUrl('/status');
          utils.logout();
        });
      });
    });
  };

  it('Whistleblowers should be able to submit tips (1)', function() {
    perform_submission();
  });

  it('Whistleblowers should be able to submit tips (2)', function() {
    perform_submission();
  });

  it('Whistleblowers should be able to submit tips (3)', function() {
    perform_submission();
  });

  it('Whistleblower should be able to access the first submission', function() {
    utils.login_whistleblower(receipts[0]);
    expect(element(by.xpath("//*[contains(text(),'" + tip_text + "')]")).getText()).toEqual(tip_text);
    utils.logout();
  });

  it('Recipient should be able to access and label the first submission', function() {
    var label_1 = 'seems interesting.';
    var label_2 = 'it\'s a trap!';

    utils.login_receiver();

    element(by.id('tip-0')).evaluate('tip.id').then(function(id) {
     utils.logout('/login');
     utils.login_receiver(receiver_username, receiver_password, '/#/status/' + id);

     // Configure label_1
     expect(element(by.xpath("//*[contains(text(),'" + tip_text + "')]")).getText()).toEqual(tip_text);
     element(by.model('tip.label')).sendKeys(label_1);
     element(by.id('assignLabelButton')).click();

     // Check presence of label_1
     expect(element(by.id('assignLabelButton')).isPresent()).toBe(false);
     expect(element(by.id('Label')).getText()).toEqual(label_1);

     // Configure label_2
     element(by.id('Label')).click();
     element(by.model('tip.label')).clear().sendKeys(label_2);
     element(by.id('assignLabelButton')).click();
    });
  });

  it('Recipient should be able to see files and download them', function() {
    if (!utils.testFileUpload()) {
      return;
    }

    expect(element.all(by.cssContainingText("button", "download")).count()).toEqual(2);

    if (!utils.testFileDownload()) {
      return;
    }

    element.all(by.cssContainingText("button", "download")).get(0).click().then(function() {
      browser.waitForAngular();
    });
  });

  it('Recipient should be able to leave a comment to the whistleblower', function() {
    utils.login_receiver();

    element(by.id('tip-0')).click().then(function() {
      element(by.model('tip.newCommentContent')).sendKeys(comment);
      element(by.id('comment-action-send')).click().then(function() {
        browser.waitForAngular();
        element(by.id('comment-0')).element(by.css('.preformatted')).getText().then(function(c) {
          expect(c).toContain(comment);
          utils.logout('/login');
        });
      });
    });
  });

  it('Whistleblower should be able to read the comment from the receiver and reply', function() {
    utils.login_whistleblower(receipts[0]);

    element(by.id('comment-0')).element(by.css('.preformatted')).getText().then(function(c) {
      expect(c).toEqual(comment);
      element(by.model('tip.newCommentContent')).sendKeys(comment_reply);
      element(by.id('comment-action-send')).click().then(function() {
        browser.waitForAngular();
        element(by.id('comment-0')).element(by.css('.preformatted')).getText().then(function(c) {
          expect(c).toContain(comment_reply);
        });
      });
    });
  });

  it('Whistleblower should be able to attach a new file to the first submission', function() {
    if (!utils.testFileUpload()) {
      return;
    }

    utils.login_whistleblower(receipts[0]);

    browser.executeScript('angular.element(document.querySelector(\'input[type="file"]\')).attr("style", "opacity:0; visibility: visible;");');
    element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload).then(function() {
      browser.waitForAngular();
      element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload).then(function() {
        browser.waitForAngular();
        // TODO: test file addition
        utils.logout();
      });
    });
  });

  it('Recipient should be able to start a private discussion with the whistleblower', function() {
    utils.login_receiver();

    element(by.id('tip-0')).click().then(function() {
      element(by.model('tip.newMessageContent')).sendKeys(message);
      element(by.id('message-action-send')).click().then(function() {
        browser.waitForAngular();
        element(by.id('message-0')).element(by.css('.preformatted')).getText().then(function(m) {
          expect(m).toContain(message);
          utils.logout('/login');
        });
      });
    });
  });

  it('Whistleblower should be able to read the private message from the receiver and reply', function() {
    utils.login_whistleblower(receipts[0]);

    element.all(by.options("obj.key as obj.value for obj in tip.msg_receivers_selector | orderBy:'value'")).get(1).click().then(function() {
      element(by.id('message-0')).element(by.css('.preformatted')).getText().then(function(message1) {
        expect(message1).toEqual(message);
        element(by.model('tip.newMessageContent')).sendKeys(message_reply);
        element(by.id('message-action-send')).click().then(function() {
          browser.waitForAngular();
          element(by.id('message-0')).element(by.css('.preformatted')).getText().then(function(message2) {
            expect(message2).toContain(message_reply);
          });
        });
      });
    });
  });

  it('Recipient should be able to export the submission', function() {
    if (utils.testFileDownload()) {
      return;
    }

    utils.login_receiver();
    element(by.id('tip-0')).click();
    element(by.id('tipFileName')).getText().then(function(t) {
      expect(t).toEqual(jasmine.any(String));
      if (!utils.verifyFileDownload()) {
        return;
      }

      var fullpath = path.resolve(path.join(browser.params.tmpDir, t));
      utils.waitForFile(fullpath + '.zip');
    });
  });

  it('Recipient should be able to disable and renable email notifications', function() {
    utils.login_receiver();

    element(by.id('tip-0')).click();

    utils.waitUntilPresent(by.id('tip-action-silence'));

    var silence = element(by.id('tip-action-silence'));
    silence.click();
    var notif = element(by.id('tip-action-notify'));
    notif.evaluate('tip.enable_notifications').then(function(enabled) {
      expect(enabled).toEqual(false);
      notif.click();
      silence.evaluate('tip.enable_notifications').then(function(enabled) {
        expect(enabled).toEqual(true);
        // TODO Determine if emails are actually blocked.
      });
    });
  });

  it('Recipient should be able to postpone all tips', function() {
    utils.login_receiver();

    element.all(by.css('#tipListTableBody tr'))
        .evaluate('tip.expiration_date').then(function(exprs) {
      // Postpone the expiration of all tips
      element(by.id('tip-action-select-all')).click();
      element(by.id('tip-action-postpone-selected')).click();
      element(by.id('modal-action-ok')).click();
      // Collect the new later expiration dates.
      element.all(by.css('#tipListTableBody tr')).evaluate('tip.expiration_date').then(function(exprs) {
        // TODO
        // It is currently impossible to test that the expiration date is update because
        // during the same day of the submission a postpone will result in the same expiration date
      }
      });
    });
  });

  it('Recipient should be able to postpone first submission from its tip page', function() {
    utils.login_receiver();

    element(by.id('tip-0')).click();
    // Get the tip's original expiration date.
    element(by.id('tipFileName')).evaluate('tip.expiration_date').then(function(d) {
      expect(d).toEqual(jasmine.any(String));
      var startExpiration = new Date(d);
      element(by.id('tip-action-postpone')).click();
      element(by.id('modal-action-ok')).click();

      element(by.id('tipFileName')).evaluate('tip.expiration_date').then(function(d) {
        expect(d).toEqual(jasmine.any(String));
        var newExpiration = new Date(d);
        expect(newExpiration).toBeGreaterThan(startExpiration);
      });
    });
  });

  it('Recipient should be able to delete third submission from its tip page', function() {
    utils.login_receiver();

    // Find the uuid of the first tip.
    element(by.id('tip-2')).click();
    element(by.id('tipFileName')).evaluate('tip.id').then(function(tip_uuid) {
      element(by.id('tip-action-delete')).click();
      element(by.id('modal-action-ok')).click();

      // Ensure that the tip has disappeared from the recipient's view.
      element.all(by.css('#tipListTableBody tr')).evaluate('tip.id').then(function(uuids) {
        var i = uuids.indexOf(tip_uuid);
        expect(i).toEqual(-1);
        utils.logout('/login');
      });
    });
  });
});
