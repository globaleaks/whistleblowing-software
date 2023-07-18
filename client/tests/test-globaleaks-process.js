describe("globaleaks process", function() {
  var N = 3;
  var receipts = [];
  var comment = "comment";
  var comment_reply = "comment reply";

  var perform_submission = async function() {
    var wb = new browser.gl.pages.whistleblower();
    var receipt = await wb.performSubmission(true);
    receipts.unshift(receipt);
  };

  for (var i=1; i<N; i++) {
    it("Whistleblowers should be able to perform a submission", async function() {
      await perform_submission();
    });

    it("Recipient should be able to access, label and mark as important the last submission", async function() {
      await browser.gl.utils.login_receiver();
      await browser.setLocation("/recipient/reports");

      var id = await element(by.id("tip-0")).evaluate("tip.id");

      await browser.setLocation("/status/" + id);

      expect(await element(by.xpath("//*[contains(text(),'summary')]")).getText()).toEqual("summary");

      await element(by.model("tip.label")).sendKeys("Important");
      await element(by.id("assignLabelButton")).click();

      await element(by.id("tip-action-star")).click();
    });

    it("Recipient should be able to see files and download them", async function() {
      expect(await element.all(by.css(".tip-action-download-file")).count()).toEqual(2);

      await element.all(by.css(".tip-action-download-file")).get(0).click();
    });

    it("Recipient should be able to leave a comment to the whistleblower", async function() {
      await element(by.model("tip.newCommentContent")).sendKeys(comment);
      await element(by.id("comment-action-send")).click();

      var c = await element(by.id("comment-0")).element(by.css(".preformatted")).getText();

      expect(c).toContain(comment);

      await browser.setLocation("/recipient/reports");
      await browser.gl.utils.takeScreenshot("recipient/reports.png");

      await browser.gl.utils.logout();
    });

    it("Whistleblower should be able to read the comment from the receiver and reply", async function() {
      await browser.gl.utils.login_whistleblower(receipts[0]);

      var c = await element(by.id("comment-0")).element(by.css(".preformatted")).getText();
      expect(c).toEqual(comment);

      await element(by.model("tip.newCommentContent")).sendKeys(comment_reply);
      await element(by.id("comment-action-send")).click();

      c = await element(by.id("comment-0")).element(by.css(".preformatted")).getText();
      expect(c).toContain(comment_reply);

      await browser.gl.utils.takeScreenshot("whistleblower/report.png");
    });

    it("Whistleblower should be able to attach a new file to the last submission", async function() {
      var fileToUpload = browser.gl.utils.makeTestFilePath("evidence-3.txt");
      await element(by.xpath("//input[@type='file']")).sendKeys(fileToUpload);
      await element(by.id("files-action-confirm")).click();
      await browser.gl.utils.waitUntilPresent(by.css(".progress-bar-complete"));

      await browser.gl.utils.logout();
    });

    it("Recipient should be able to export the submission", async function() {
      await browser.gl.utils.login_receiver();
      await browser.setLocation("/recipient/reports");

      var id = await element(by.id("tip-0")).evaluate("tip.id");
      await browser.setLocation("/status/" + id);
      await browser.gl.utils.waitUntilPresent(by.id("tip-action-export"));
      await element(by.id("tip-action-export")).click();

      var t = await element.all(by.css(".TipInfoID")).first().getText();
      expect(t).toEqual(jasmine.any(String));
      await browser.gl.utils.logout();
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

      await browser.gl.utils.takeScreenshot("recipient/report.png");
      await browser.gl.utils.logout();
    });
  }
});
