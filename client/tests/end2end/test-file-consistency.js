var fs = require('fs');
var path = require('path');

var openpgp = require('openpgp');

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
        var mfile = test_meta_files[i];
        mfile.waitForDownloadAndVerifyCheckSum();
      });
    });
  });

  it('uploaded and encrypted files should match downloaded and decrypted files', function(done) {
    if (!browser.gl.utils.testFileUpload() || !browser.gl.utils.testFileDownload() || !browser.gl.utils.verifyFileDownload()) {
      done();
      return;
    }

    var wb = new browser.gl.pages.whistleblower();
    var rec = new browser.gl.pages.receiver();

    var opts = { encoding: 'utf8', flag: 'r' };
    var priv_key = fs.readFileSync('../backend/globaleaks/tests/data/gpg/VALID_PGP_KEY1_PRV', opts);
    var pub_key = fs.readFileSync('../backend/globaleaks/tests/data/gpg/VALID_PGP_KEY1_PUB', opts);

    wb.performSubmission('Test file openpgp consistency', false).then(function(receipt) {
      // attach files to submission
      wb.viewReceipt(receipt);
      test_meta_files.forEach(function(m_file) {
        wb.submitFile(m_file.origin_path);
      });

      browser.gl.utils.logout();

      browser.gl.utils.login_receiver('recipient', browser.gl.utils.vars['user_password']);
      rec.viewMostRecentSubmission();

      var files_sel = by.cssContainingText("button", "download");
      expect(element.all(files_sel).count()).toBe(test_meta_files.length);

      element.all(files_sel).each(function(btn, i) {
        btn.click();

        // TODO WARN fragile: dl list and meta_file_lst must align
        var m_file = test_meta_files[i];
        var full_path = m_file.tmp_path + '.pgp';
        browser.gl.utils.waitForFile(full_path).then(function() {
          var data = fs.readFileSync(full_path, opts);

          var options = {
            message: openpgp.message.readArmored(data),
            publicKeys: openpgp.key.readArmored(pub_key),
            privateKey: openpgp.key.readArmored(priv_key).keys[0],
          };

          openpgp.decrypt(options).then(function(result) {
            expect(result.valid).toBeTrue();

            // check the files to see if they match
            var test = browser.gl.utils.checksum(result.data);
            expect(test).toEqual(m_file.chksum);

            done();
          });
        });
      });
    });
  });

  it('the recipient should be able to upload wbfiles', function() {
    if (!browser.gl.utils.testFileUpload()) return;

    wb.performSubmission('Test WBFile process').then(function(r) {
      receipt = r;

      browser.gl.utils.login_receiver('recipient', browser.gl.utils.vars['user_password']);

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
