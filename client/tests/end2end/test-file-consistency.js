var fs = require('fs');
var path = require('path');

var openpgp = require('openpgp');

var pages = require('./pages.js');
var utils = require('./utils.js');


function TmpFileMeta(filename) {
    this.name = filename;
    this.origin_path = utils.makeTestFilePath(filename);
    this.tmp_path = path.join(browser.params.tmpDir, filename);

    this.unlinkTmpPath();

    var s = fs.readFileSync(this.origin_path);
    var c = utils.checksum(s);
    this.chksum = c;
    if (browser.params.verifyFileDownload) {
      this.waitForDownload = function() {}; // noop
    }
}

TmpFileMeta.prototype.unlinkTmpPath = function(){
    if (fs.existsSync(this.tmp_path)) {
      fs.unlinkSync(this.tmp_path);
    }
};

TmpFileMeta.prototype.waitForDownload = function() {
  var self = this;
  utils.waitForFile(self.tmp_path).then(function() {
      var tmp_sum = utils.checksum(fs.readFileSync(self.tmp_path));
      expect(tmp_sum).toEqual(self.chksum);
      // Remove the tmp file before moving on. (it could be used again)
      fs.unlinkSync(self.tmp_path);
  });
};


var test_meta_files = fs.readdirSync(utils.vars.testFileDir).map(function(name) {
  return new TmpFileMeta(name);
});


// TODO File types left to test:
// docx, ppt, mp4, mp3, wav, html, zip, > 30mb
describe('Submission whistleblower file upload process', function() {

  beforeEach(function() {
    test_meta_files.forEach(function(meta_file) {
      meta_file.unlinkTmpPath();
    });
  });

  function uploadAndDownloadTest() {
    var wb = new pages.whistleblower();
    var rec = new pages.receiver();

    wb.performSubmission('Test file consistency').then(function(receipt) {
      wb.viewReceipt(receipt);

      // Add each file as an attachment.
      test_meta_files.forEach(function(m_file) {
        wb.submitFile(m_file.origin_path);
      });

      utils.logout();

      // Login as the receiver
      utils.login_receiver('Recipient2', utils.vars['user_password']);
      rec.viewMostRecentSubmission();

      // Download each file end assert that it matches the input
      element.all(by.cssContainingText("button", "download")).each(function(btn, i) {
        btn.click();
        // TODO WARN fragile: dl list and meta_file_lst must align
        var mfile = test_meta_files[i];
        mfile.waitForDownload();
      });
    });
  }

  function uploadAndDecryptTest() {
    var wb = new pages.whistleblower();
    var rec = new pages.receiver();

    var opts = { encoding: 'utf8', flag: 'r' };
    var priv_key = fs.readFileSync('../backend/globaleaks/tests/keys/VALID_PGP_KEY1_PRV', opts);
    var pub_key = fs.readFileSync('../backend/globaleaks/tests/keys/VALID_PGP_KEY1_PUB', opts);

    wb.performSubmission('Test file openpgp consistency').then(function(receipt) {
      // attach files to submission
      wb.viewReceipt(receipt);

      test_meta_files.forEach(function(m_file) {
        wb.submitFile(m_file.origin_path);
      });

      utils.logout();

      utils.login_receiver('Recipient1', utils.vars['user_password']);
      rec.viewMostRecentSubmission();

      element.all(by.cssContainingText("button", "download")).each(function(btn, i) {
        btn.click();

        // TODO WARN fragile: dl list and meta_file_lst must align
        var m_file = test_meta_files[i];
        var full_path = m_file.tmp_path + '.pgp';
        utils.waitForFile(full_path).then(function() {
          var data = fs.readFileSync(full_path, opts);

          var options = {
            message: openpgp.message.readArmored(data),
            publicKeys: pub_key,
            privateKey: priv_key,
          };

          openpgp.decrypt(options).then(function(result) {
            expect(result.valid).toBeTrue();

            // check the files to see if they match
            var test = utils.checksum(result.data);
            expect(test).toEqual(m_file.chksum);
          });
        });
      });
    });
  }

  if (browser.params.verifyFileDownload) {
    it('uploaded and downloaded plaintext files should match', uploadAndDownloadTest);
    it('uploaded and encrypted files should match downloaded and decrypted files', uploadAndDecryptTest);
  }
});

describe('Tip wbfile upload process', function() {
    var wb = new pages.whistleblower();
    var rec = new pages.receiver();

    var f1_info = test_meta_files[4];
    f1_info.unlinkTmpPath(); // cleanup
    var f1_text = 'file to show to the whistleblower';
    var f2_info = test_meta_files[5];

    var receipt;


    it('the recipient should be able to upload wbfiles', function() {
      wb.performSubmission('Test WBFile process').then(function(r) {
        receipt = r;

        utils.login_receiver('Recipient1', utils.vars['user_password']);

        element(by.id('tip-0')).click();

        rec.wbfile_widget().element(by.css('input[type="text"]')).sendKeys(f1_text);
        rec.wbfile_widget().element(by.css('.input-group-btn button')).click();
        rec.uploadWBFile(f1_info.origin_path);

        rec.wbfile_widget().element(by.css('input[type="text"]')).sendKeys('wbfile to delete');
        rec.wbfile_widget().element(by.css('.input-group-btn button')).click();
        rec.uploadWBFile(f2_info.origin_path);

        expect(rec.wbfile_widget().element(by.css('#wbfile-0 p.description')).getText())
          .toEqual('Description: ' + f1_text);

        // Assert that the uploads worked
        expect(rec.wbfile_widget().all(by.css('div.wbfile')).count()).toEqual(2);
   });

   it('the recipient should be able to downlad a wbfile', function() {
        // Let the reciever download the first file
        rec.wbfile_widget().element(by.css('#wbfile-0 span.btn span.glyphicon-download')).click();

        f1_info.waitForDownload();
    });

    it('a recipient should be able to delete a wbfile', function() {
        // Delete the second wbfile
        rec.wbfile_widget().element(by.css('#wbfile-1 span span.glyphicon-trash')).click();
        // Assert the file is gone from the interfaccia
        expect(rec.wbfile_widget().all(by.css('div.wbfile')).count()).toEqual(1);

        utils.logout();
    });

    it('a whistleblower should be able to download wbfiles', function() {
        utils.login_whistleblower(receipt);
        // Choose the first file which should be f1_info
        element(by.css('#AttachedWBFile #wbfile-0 div.download-btn')).click();
        f1_info.waitForDownload();
      });
    });
});
