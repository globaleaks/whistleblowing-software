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
describe('test file consistency', function() {

  var r_username = "Recipient 1";
  var r_password = "ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#";

  var testFileDir = './tests/end2end/files/';

  var filenames = fs.readdirSync(testFileDir);
  var dirs = filenames.map(function(files) { 
    return path.resolve(path.join(testFileDir, files));
  });

  var chksums = {};

  for (var i = 0; i < dirs.length; i++) {
    var s = fs.readFileSync(dirs[i]);
    var c = checksum(s);
    chksums[filenames[i]] = c;
  }

  function uploadAndDownload() {
    var wb = new pages.whistleblower();
    var rec = new pages.receiver();
    
    wb.performSubmission('Test file consistency').then(function(receipt) {

      wb.viewReceipt(receipt);
      
      // Add each file as an attachment.
      dirs.forEach(function(name) {
        wb.submitFile(name); 
      });

      wb.logout();
      
      // Login as the receiver
      rec.login(r_username, r_password);
      rec.viewMostRecentSubmission();

      // Download each file
      element.all(by.cssContainingText("button", "download")).each(function(btn, i) {
        btn.click();
        browser.waitForAngular();

        var name = filenames[i];
        var fullpath = path.resolve(path.join(browser.params.tmpDir, name));
        utils.waitForFile(fullpath, 2000).then(function() {
          // Check that each downloaded file matches its original
          var test = checksum(fs.readFileSync(fullpath));
          expect(test).toEqual(chksums[name]);
        });
      });

    });
  }

  if (browser.params.verifyFileDownload) {
    it('Upload and download of file should match', uploadAndDownload);
  }

});
