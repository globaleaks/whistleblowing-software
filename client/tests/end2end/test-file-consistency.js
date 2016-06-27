var crypto = require('crypto');
var fs = require('fs');
var path = require('path');

var pages = require('./pages.js');
var utils = require('./utils.js');

function checksum(input) {
  return crypto.createHash('sha1').update(input, 'utf8').digest('hex');
}

// File types left to test:
// docx, doc, ppt, mp4, mp3, wav, html, zip
describe('Submission file process', function() {
  var testFileDir = './tests/end2end/files/';

  var filenames = fs.readdirSync(testFileDir);
  var dirs = filenames.map(function(name) {
    return path.resolve(path.join(testFileDir, name));
  });

  var chksums = {};

  for (var i = 0; i < dirs.length; i++) {
    var s = fs.readFileSync(dirs[i]);
    var c = checksum(s);
    chksums[filenames[i]] = c;
  }

  beforeEach(function() {
    filenames.forEach(function(t) {
      try {
        fs.unlinkSync(path.join(browser.params.tmpDir, t));
      } catch (e) {
        /* eslint-disable no-console */
        // No-op to surpress noisy output
        // console.error(e);
        /* eslint-enable no-console */
      }
    });
  });


  if (browser.params.verifyFileDownload) {
    it('uploaded and downloaded plaintext files should match', function() {
      var wb = new pages.whistleblower();
      var rec = new pages.receiver();

      wb.performSubmission('Test file consistency').then(function(receipt) {
        wb.viewReceipt(receipt);

        // Add each file as an attachment.
        dirs.forEach(function(name) {
          wb.submitFile(name); 
        });

        utils.logout();

        // Login as the receiver
        utils.login_receiver('Recipient2', utils.vars['user_password']);
        rec.viewMostRecentSubmission();

        // Download each file
        element.all(by.cssContainingText("button", "download")).each(function(btn, i) {
          btn.click();
          browser.waitForAngular();

          var name = filenames[i];
          var fullpath = path.resolve(path.join(browser.params.tmpDir, name));
          utils.waitForFile(fullpath, 2000).then(function() {
            // Check that each downloaded file's checksum matches its original
            var test = checksum(fs.readFileSync(fullpath));
            expect(test).toEqual(chksums[name]);
          });
        });
      });
    });   
  }
});
