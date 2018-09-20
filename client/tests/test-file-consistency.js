var fs = require('fs');
var path = require('path');

function TmpFileMeta(filename) {
  this.name = filename;
  this.origin_path = browser.gl.utils.makeTestFilePath(filename);
  this.tmp_path = path.join(browser.params.tmpDir, filename);

  this.unlinkTmpPath();

  var s = fs.readFileSync(this.origin_path);
  this.chksum = browser.gl.utils.checksum(s);
}

TmpFileMeta.prototype.unlinkTmpPath = function(){
  if (fs.existsSync(this.tmp_path)) {
    fs.unlinkSync(this.tmp_path);
  }
};

TmpFileMeta.prototype.waitForDownload = function() {
  var self = this;
  return browser.gl.utils.waitForFile(self.tmp_path);
};

TmpFileMeta.prototype.waitForDownloadAndVerifyCheckSum = function() {
  var self = this;
  browser.gl.utils.waitForFile(self.tmp_path).then(function() {
    var tmp_sum = browser.gl.utils.checksum(fs.readFileSync(self.tmp_path));
    expect(tmp_sum).toEqual(self.chksum);
    // Remove the tmp file before moving on. (it could be used again)
    fs.unlinkSync(self.tmp_path);
  });
};


var test_meta_files = fs.readdirSync(browser.gl.utils.vars.testFileDir).map(function(name) {
  return new TmpFileMeta(name);
});


describe('Test file upload/download consistency', function() {
  var wb = new browser.gl.pages.whistleblower();
  var rec = new browser.gl.pages.receiver();

  var f1_info = test_meta_files[4];
  f1_info.unlinkTmpPath(); // cleanup
  var f1_text = 'file to show to the whistleblower';
  var f2_text = 'file to show to upload and then delete';
  var f2_info = test_meta_files[5];

  var receipt;

  // TODO File types left to test:
  // docx, ppt, mp4, mp3, wav, html, zip, > 30mb

  beforeEach(function() {
    test_meta_files.forEach(function(meta_file) {
      meta_file.unlinkTmpPath();
    });
  });

  it('uploaded and downloaded plaintext files should match', function() {
    if (!browser.gl.utils.testFileUpload() || !browser.gl.utils.testFileDownload() || !browser.gl.utils.verifyFileDownload()) return;

    var wb = new browser.gl.pages.whistleblower();
    var rec = new browser.gl.pages.receiver();

    wb.performSubmission('Test file consistency', false).then(function(receipt) {
      wb.viewReceipt(receipt);
       // Add each file as an attachment.
      test_meta_files.forEach(function(m_file) {
        wb.submitFile(m_file.origin_path);
      });

      browser.gl.utils.logout();

      // Login as the receiver
      browser.gl.utils.login_receiver('Recipient2', browser.gl.utils.vars['user_password']);
      rec.viewMostRecentSubmission();

      var files_sel = by.cssContainingText("button", "download");
      expect(element.all(files_sel).count()).toBe(test_meta_files.length);

      // Download each file and assert that it matches the input
      element.all(files_sel).each(function(btn, i) {
        btn.click();
        // TODO WARN fragile: dl list and meta_file_lst must align
        test_meta_files[i].waitForDownloadAndVerifyCheckSum();
      });
    });
  });

  it('the recipient should be able to upload wbfiles', function() {
    if (!browser.gl.utils.testFileUpload()) return;

    wb.performSubmission('Test WBFile process').then(function(r) {
      receipt = r;

      browser.gl.utils.login_receiver('recipient', browser.gl.utils.vars['user_password']);
      browser.setLocation('/receiver/tips');

      element(by.id('tip-0')).click();

      rec.wbfile_widget().element(by.css('input[type="text"]')).sendKeys(f1_text);
      rec.uploadWBFile(f1_info.origin_path);

      browser.gl.utils.waitUntilPresent(by.css('#wbfile-0 p.description')).then(function() {
        expect(rec.wbfile_widget().element(by.css('#wbfile-0 p.description')).getText())
          .toEqual('Description: ' + f1_text);

        browser.gl.utils.waitUntilPresent(by.css('#TipPageWBFileUpload input[type="text"]')).then(function() {
          rec.wbfile_widget().element(by.css('input[type="text"]')).sendKeys(f2_text);
          rec.uploadWBFile(f2_info.origin_path);

          browser.gl.utils.waitUntilPresent(by.css('#wbfile-1 p.description')).then(function() {
            expect(rec.wbfile_widget().element(by.css('#wbfile-1 p.description')).getText())
              .toEqual('Description: ' + f2_text);
          });
        });
      });
    });
  });

  it('a recipient should be able to delete a wbfile', function() {
    if (!browser.gl.utils.testFileUpload()) return;

    // Delete the second wbfile
    rec.wbfile_widget().element(by.css('#wbfile-1 span span.glyphicon-trash')).click();
    // Assert the file is gone from the interfaccia
    expect(rec.wbfile_widget().all(by.css('div.wbfile')).count()).toEqual(1);
  });

  it('the recipient should be able to downlad a wbfile', function() {
    if (!browser.gl.utils.testFileUpload() || !browser.gl.utils.testFileDownload()) return;

    // Let the reciever download the first file
    rec.wbfile_widget().element(by.css('#wbfile-0 span.btn span.glyphicon-download')).click();
    f1_info.waitForDownload();
  });

  it('a whistleblower should be able to download wbfiles', function() {
    if (!browser.gl.utils.testFileUpload() || !browser.gl.utils.testFileDownload()) return;

    browser.gl.utils.login_whistleblower(receipt);
    // Choose the first file which should be f1_info
    element(by.css('#AttachedWBFile #wbfile-0 div.download-button')).click();
    f1_info.waitForDownload();
  });
});
