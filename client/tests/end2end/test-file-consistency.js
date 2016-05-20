var crypto = require('crypto');
var fs = require('fs');
var path = require('path');
var pages = require('./pages.js');

function checksum(input) {
  return crypto.createHash('sha1').update(input, 'utf8').digest('hex');
}

describe('file consistency', function() {

  var r_username = "Recipient 1";
  var r_password = "ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#";

  var testFileDir = './tests/end2end/files/';
  var tmpFileDir = './tests/end2end/tmp/';

  var dirs = fs.readdirSync(testFileDir);
  // File types to test:
  // pdf, docx, doc, ppt, png, jpeg, jpg, mp4, mp3, wav, txt, html, zip
  var chksums = {};

  dirs.forEach(function(name) {
    var s = fs.readFileSync(path.join(testFileDir, name));
    var c = checksum(s);
    chksums[name] = c;
    console.log(name, checksum(s));
  });

  it('Upload and download of file should match', function() {
    var wb = new pages.whistleblower();
    var rec = new pages.receiver();
    wb.performSubmission().then(function(receipt) {
      // Add each file as an attachment.
      
      rec.login(r_username, r_password).then(function() {
        // Login as the receiver
        
        // Download each file

        // Check that the files match.

      });

    });
  
  });


});
