var path = require('path');

var fileToUpload1 = browser.gl.utils.makeTestFilePath('antani.txt');
var fileToUpload2 = browser.gl.utils.makeTestFilePath('unknown.filetype');

describe('globaLeaks process', function() {
  var tip_text = 'topsecret';
  var receipts = [];
  var comment = 'comment';
  var comment_reply = 'comment reply';
  var message = 'message';
  var message_reply = 'message reply';
  var receiver_username = "recipient";
  var receiver_password = browser.gl.utils.vars['user_password'];

  var perform_submission = function() {
    var wb = new browser.gl.pages.whistleblower();
    wb.performSubmission(tip_text, true).then(function(receipt) {
      receipts.unshift(receipt);
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

  it('Whistleblower should be able to access the last submission', function() {
    browser.gl.utils.login_whistleblower(receipts[2]);
    expect(element(by.xpath("//*[contains(text(),'" + tip_text + "')]")).getText()).toEqual(tip_text);
    browser.gl.utils.logout();
  });

  it('Recipient should be able to access and label the last submission', function() {
    var label_1 = 'seems interesting.';
    var label_2 = 'it\'s a trap!';

    browser.gl.utils.login_receiver();

    element(by.id('tip-0')).evaluate('tip.id').then(function(id) {
     browser.gl.utils.logout('/login');
     browser.gl.utils.login_receiver(receiver_username, receiver_password, '/#/status/' + id);

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
    if (!browser.gl.utils.testFileUpload()) {
      return;
    }

    expect(element.all(by.cssContainingText("button", "download")).count()).toEqual(2);

    if (!browser.gl.utils.testFileDownload()) {
      return;
    }

    element.all(by.cssContainingText("button", "download")).get(0).click().then(function() {
      browser.waitForAngular();
    });
  });

  it('Recipient should be able to leave a comment to the whistleblower', function() {
    browser.gl.utils.login_receiver();

    element(by.id('tip-0')).click().then(function() {
      element(by.model('tip.newCommentContent')).sendKeys(comment);
      element(by.id('comment-action-send')).click().then(function() {
        browser.waitForAngular();
        element(by.id('comment-0')).element(by.css('.preformatted')).getText().then(function(c) {
          expect(c).toContain(comment);
          browser.gl.utils.logout('/login');
        });
      });
    });
  });

  it('Whistleblower should be able to read the comment from the receiver and reply', function() {
    browser.gl.utils.login_whistleblower(receipts[0]);

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

  it('Whistleblower should be able to attach a new file to the last submission', function() {
    if (!browser.gl.utils.testFileUpload()) {
      return;
    }

    browser.gl.utils.login_whistleblower(receipts[0]);

    browser.executeScript('angular.element(document.querySelector(\'input[type="file"]\')).attr("style", "visibility: visible;");');
    element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload1).then(function() {
      browser.waitForAngular();
      element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload2).then(function() {
        browser.waitForAngular();
        // TODO: test file addition
        browser.gl.utils.logout();
      });
    });
  });

  it('Recipient should be able to start a private discussion with the whistleblower', function() {
    browser.gl.utils.login_receiver();

    element(by.id('tip-0')).click().then(function() {
      element(by.model('tip.newMessageContent')).sendKeys(message);
      element(by.id('message-action-send')).click().then(function() {
        browser.waitForAngular();
        element(by.id('message-0')).element(by.css('.preformatted')).getText().then(function(m) {
          expect(m).toContain(message);
          browser.gl.utils.logout('/login');
        });
      });
    });
  });

  it('Whistleblower should be able to read the private message from the receiver and reply', function() {
    browser.gl.utils.login_whistleblower(receipts[0]);

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
    if (!browser.gl.utils.testFileDownload()) {
      return;
    }

    browser.gl.utils.login_receiver();
    element(by.id('tip-0')).click();

    browser.gl.utils.waitUntilPresent(by.id('tip-action-export'));

    element(by.id('tip-action-export')).click();

    element(by.id('tipID')).getText().then(function(t) {
      expect(t).toEqual(jasmine.any(String));
      if (!browser.gl.utils.verifyFileDownload()) {
        return;
      }

      var fullpath = path.resolve(path.join(browser.params.tmpDir, t));
      browser.gl.utils.waitForFile(fullpath + '.zip');
    });
  });

  it('Recipient should be able to disable and renable email notifications', function() {
    browser.gl.utils.login_receiver();

    element(by.id('tip-0')).click();

    browser.gl.utils.waitUntilPresent(by.id('tip-action-silence'));

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
    browser.gl.utils.login_receiver();

    element.all(by.css('#tipListTableBody tr'))
        .evaluate('tip.expiration_date').then(function() {
      // Postpone the expiration of all tips
      element(by.id('tip-action-select-all')).click();
      element(by.id('tip-action-postpone-selected')).click();
      element(by.id('modal-action-ok')).click();
      // Collect the new later expiration dates.
      element.all(by.css('#tipListTableBody tr')).evaluate('tip.expiration_date').then(function() {
        // TODO
        // It is currently impossible to test that the expiration date is update because
        // during the same day of the submission a postpone will result in the same expiration date
      });
    });
  });

  it('Recipient should be able to postpone last submission from its tip page', function() {
    browser.gl.utils.login_receiver();

    element(by.id('tip-0')).click();
    // Get the tip's original expiration date.
    element(by.id('tipID')).evaluate('tip.expiration_date').then(function() {
      element(by.id('tip-action-postpone')).click();
      element(by.id('modal-action-ok')).click();

      element(by.id('tipID')).evaluate('tip.expiration_date').then(function() {
        // TODO
        // It is currently impossible to test that the expiration date is update because
        // during the same day of the submission a postpone will result in the same expiration date
      });
    });
  });

  it('Recipient should be able to delete third submission from its tip page', function() {
    browser.gl.utils.login_receiver();

    // Find the uuid of the first tip.
    element(by.id('tip-0')).click();
    element(by.id('tip-action-delete')).click();
    element(by.id('modal-action-ok')).click();
  });
});
