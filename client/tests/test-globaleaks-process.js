var path = require("path");

var fileToUpload1 = browser.gl.utils.makeTestFilePath("20mb.dat");
var fileToUpload2 = browser.gl.utils.makeTestFilePath("unknown.filetype");

describe("globaLeaks process", function() {
  var tip_text = "topsecret";
  var receipts = [];
  var comment = "comment";
  var comment_reply = "comment reply";
  var message = "message";
  var message_reply = "message reply";

  var perform_submission = async function() {
    var wb = new browser.gl.pages.whistleblower();
    var receipt = await wb.performSubmission(tip_text, true);
    receipts.unshift(receipt);
  };

  it("Whistleblowers should be able to submit tips (1)", async function() {
    await perform_submission();
  });

  it("Whistleblowers should be able to submit tips (2)", async function() {
    await perform_submission();
  });

  it("Whistleblowers should be able to submit tips (3)", async function() {
    await perform_submission();
  });

  it("Recipient should be able to access and label the last submission", async function() {
    var label_1 = "interesting!";
    var label_2 = "fake!";

    await browser.gl.utils.login_receiver();
    await browser.setLocation("/recipient/reports");

    var id = await element(by.id("tip-0")).evaluate("tip.id");

    await browser.setLocation("/status/" + id);

    // Configure label_1
    expect(await element(by.xpath("//*[contains(text(),'" + tip_text + "')]")).getText()).toEqual(tip_text);
    await element(by.model("tip.label")).sendKeys(label_1);
    await element(by.id("assignLabelButton")).click();

    // Check presence of label_1
    expect(await element(by.id("assignLabelButton")).isPresent()).toBe(false);
    expect(await element(by.id("Label")).getText()).toEqual(label_1);

    // Configure label_2
    await element(by.id("Label")).click();
    await element(by.model("tip.label")).clear();
    await element(by.model("tip.label")).sendKeys(label_2);
    await element(by.id("assignLabelButton")).click();
  });

  it("Recipient should be able to see files and download them", async function() {
    if (!browser.gl.utils.testFileUpload()) {
      return;
    }

    expect(await element.all(by.cssContainingText("button", "download")).count()).toEqual(2);

    if (!browser.gl.utils.testFileDownload()) {
      return;
    }

    await element.all(by.cssContainingText("button", "download")).get(0).click();
  });

  it("Recipient should be able to leave a comment to the whistleblower", async function() {
    await browser.gl.utils.login_receiver();
    await browser.setLocation("/recipient/reports");

    var id = await element(by.id("tip-0")).evaluate("tip.id");

    await browser.setLocation("/status/" + id);
    await element(by.model("tip.newCommentContent")).sendKeys(comment);
    await element(by.id("comment-action-send")).click();

    var c = await element(by.id("comment-0")).element(by.css(".preformatted")).getText();

    expect(c).toContain(comment);
    await browser.gl.utils.logout("/login");
  });

  it("Whistleblower should be able to read the comment from the receiver and reply", async function() {
    await browser.gl.utils.login_whistleblower(receipts[0]);

    var c = await element(by.id("comment-0")).element(by.css(".preformatted")).getText();
    expect(c).toEqual(comment);

    await element(by.model("tip.newCommentContent")).sendKeys(comment_reply);
    await element(by.id("comment-action-send")).click();

    c = await element(by.id("comment-0")).element(by.css(".preformatted")).getText();
    expect(c).toContain(comment_reply);
  });

  it("Whistleblower should be able to attach a new file to the last submission", async function() {
    if (!browser.gl.utils.testFileUpload()) {
      return;
    }

    await browser.gl.utils.login_whistleblower(receipts[0]);

    await element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload1);
    await browser.gl.utils.waitUntilPresent(by.cssContainingText("span", "Upload completed successfully!"));

    await element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload2);
    await browser.gl.utils.waitUntilPresent(by.cssContainingText("span", "Upload completed successfully!"));

    await browser.gl.utils.logout();
  });

  it("Recipient should be able to start a private discussion with the whistleblower", async function() {
    await browser.gl.utils.login_receiver();
    await browser.setLocation("/recipient/reports");

    var id = await element(by.id("tip-0")).evaluate("tip.id");

    await browser.setLocation("/status/" + id);
    await element(by.model("tip.newMessageContent")).sendKeys(message);
    await element(by.id("message-action-send")).click();

    var m = await element(by.id("message-0")).element(by.css(".preformatted")).getText();
    expect(m).toContain(message);

    await browser.gl.utils.logout("/login");
  });

  it("Whistleblower should be able to read the private message from the receiver and reply", async function() {
    await browser.gl.utils.login_whistleblower(receipts[0]);

    await element.all(by.options("obj.key as obj.value for obj in tip.msg_receivers_selector | orderBy:'value'")).get(1).click();
    var message1 = await element(by.id("message-0")).element(by.css(".preformatted")).getText();
    expect(message1).toEqual(message);

    await element(by.model("tip.newMessageContent")).sendKeys(message_reply);
    await element(by.id("message-action-send")).click();

    var message2 = await element(by.id("message-0")).element(by.css(".preformatted")).getText();
    expect(message2).toContain(message_reply);
  });

  it("Recipient should be able to export the submission", async function() {
    if (!browser.gl.utils.testFileDownload()) {
      return;
    }

    await browser.gl.utils.login_receiver();
    await browser.setLocation("/recipient/reports");

    var id = await element(by.id("tip-0")).evaluate("tip.id");
    await browser.setLocation("/status/" + id);
    await browser.gl.utils.waitUntilPresent(by.id("tip-action-export"));
    await element(by.id("tip-action-export")).click();

    var t = await element.all(by.css(".TipInfoID")).first().getText();
    expect(t).toEqual(jasmine.any(String));
  });

  it("Recipient should be able to disable and renable email notifications", async function() {
    await browser.gl.utils.login_receiver();
    await browser.setLocation("/recipient/reports");

    var id = await element(by.id("tip-0")).evaluate("tip.id");
    await browser.setLocation("/status/" + id);
    await browser.gl.utils.waitUntilPresent(by.id("tip-action-silence"));
    var silence = element(by.id("tip-action-silence"));
    await silence.click();

    var notif = element(by.id("tip-action-notify"));
    var enabled = await notif.evaluate("tip.enable_notifications");
    expect(enabled).toEqual(false);
    await notif.click();

    enabled = await silence.evaluate("tip.enable_notifications");
    expect(enabled).toEqual(true);
  });

  it("Recipient should be able to postpone all tips", async function() {
    await browser.gl.utils.login_receiver();
    await browser.setLocation("/recipient/reports");

    // Postpone the expiration of all tips
    await element(by.id("tip-action-select-all")).click();
    await element(by.id("tip-action-postpone-selected")).click();
    await element(by.id("modal-action-ok")).click();
  });

  it("Recipient should be able to postpone last submission from its tip page", async function() {
    await browser.gl.utils.login_receiver();
    await browser.setLocation("/recipient/reports");

    var id = await element(by.id("tip-0")).evaluate("tip.id");

    await browser.setLocation("/status/" + id);

    await element(by.id("tip-action-postpone")).click();
    await element(by.id("modal-action-ok")).click();
  });
});
