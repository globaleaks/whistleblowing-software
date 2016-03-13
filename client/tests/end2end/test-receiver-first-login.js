var utils = require('./utils.js');

var pgp_key = '-----BEGIN PGP PUBLIC KEY BLOCK-----\n' +
              'Version: GnuPG v1\n' +
              'mQINBFUlGs8BEAC8geW+vfaHNXJEbGKroFjgSywg1h8JBRB6XbDFoV2WWJKFlt51\n' +
              'd0w6U5aj4N1Xx/xpa+qPEt/oYjEouXza0JuPo0SVHhzkozSrzMjQkziSsV9NXxtp\n' +
              '3ioaat0MyOBQ1XAAn7tONCv8C7dpz+BrUXPrU+0Gh6+Q0nCR6wYtgj9ztzP4JdgW\n' +
              'fiznLQe04Ah5MB+YJEndQi12HHPUzEedX32ylmfkdxWAJ8sd+YQKRFHPWUnt8tG4\n' +
              'OOm1RORgW/P3oE1RN9VEqof2ekp+DMe5v7zWEPAWyxTKYEWaXw3p2Rv9v3cdGX3N\n' +
              't1HnA30Iqd3PeBGKwxdf/UKO5vjbzKJZcovKOdNdtvelZYWRBVZ347MEItz1mXYa\n' +
              'YNrX2L2omQ0g8ujCWRnPQSCj7UEt5wTqJ2DSftrJTCbVxa8olUSz2iaQvoJIOxBW\n' +
              'ZiwHqXc5SUdf2tuuFYmb4y/VifN5aShZKimf0KC0jwOWPVaF1EiEzMlYscvF4aDg\n' +
              'DymPdb2y9+YUGW5a2dhRCCNx7g66hruN5Q0bZHfy+bkGUN+oixunPtmV7NAMIbzF\n' +
              'pbpfkVwh+2wlwSA1zI6CL4WG8YIwQFBWq0Mfh29c3ejII0ja3A7XhYo3TzVy5Qjt\n' +
              'KBSsEZRJJQ/i9hHdvNidPYi7AvdH1FQ2koKCMHdHxM1hvHZP9/2hh5UClQARAQAB\n' +
              'tDVHaW92YW5uaSBQZWxsZXJhbm8gPGdpb3Zhbm5pLnBlbGxlcmFub0BldmlsYWxp\n' +
              'djMub3JnPokCPgQTAQIAKAUCVSUazwIbAwUJA8JnAAYLCQgHAwIGFQgCCQoLBBYC\n' +
              'AwECHgECF4AACgkQ9MvVvWeg8Yfwmg//WAisG7htbXnmK9stPcjpHaiHb/o031f5\n' +
              '8SMlhhrAKWokMDHxkZFzMdRh4OIRkdBUOQt0gDG4xdWv5AulmsVn3PegWFzQchJQ\n' +
              'IbXmdOw938iLSAustYYxVymglYWW8F6E/+yVU6JRfeAWcMzleoxpAE6NG7Mtv/U+\n' +
              'tgGUpcMuTwXz8dAPphfoc0rteiNomeAkLmdtShE2rN6Wt6wW5JA40ClqhzagmVgR\n' +
              '2bF3/4CRj1Bnjkxxza5Y5kPYHFKJWPFunJxgfQdqV8y3Y9ig09AJsmdCweK8h93T\n' +
              'p6c36CR43y6sBuHxG3G+szl4TI/Hjr+/UOTtGah0ZkcYrZV52JiulBtvtbJdAZk8\n' +
              'tIAwcMYjA9Xn0b5XY+zTdDRfZRO09lWBRahTCA7iBhz8LIWu6yn3YN2cVvFU4on5\n' +
              '8y0dVLGtilnlWm/oPCMxCTXxxrW13lSKarHLOBlGF4LHcfN2JCzPXj+a9Z2socdD\n' +
              'S9TVLJYDVd8pkUPDf0hPGr3HhCegDQU0+4kbAN7ltCJM32AKfxTjYHzjND7xbfJQ\n' +
              'IV9GwQAWttkVgMC3LqeoGPa94okGwdW6LIlpfm90z5g8stjICedCVgZtCgP/aCnr\n' +
              'OPV6OWLredhwlcgJSO76aO3l5eDyylLrQtdyjuA4yDHJ5Qnppk9ACFLcAYh9RaRp\n' +
              'BT0R5OIB7rC5Ag0EVSUazwEQALZI8/7R4n2tRjayMgC/NOQhv38Hhlz1zmNgSU8s\n' +
              'XoM04yMP1281DA3OfNoeS20cBrhzYXhFWkGuhxCY+T6Rv7YPKxc3pVr4cpz6IdCP\n' +
              '1LBW49vQU8g1w67Op3sEHYDf9OpvjOySZz89BGrGffbbrSU4lyuIb0MgZVlvwePV\n' +
              'UqtBOf1ydrhK+tPK0Um5q1sTxaL3odq2hDsgjQeu77nvptpsRlVODVACegdYA55m\n' +
              'fo4yGh3zq/WSSjd21inmYRyZ9+hfasia1yAPXIQ56U4MYtC6rm1X+7me2xEPc+Eo\n' +
              'IPYTYM7M3ssDLg15QH7wMiCBkNQzbWluZMBs/xP/4zEGB3cprit1Q7ZiXegowuZ+\n' +
              'bgK9LExwPSMnNgu9BDkfkDo+/ATlAdc0CpbCvUHwQi0ogq599zcNMCzcgexJXAkp\n' +
              '0if8OUoEf4I4/U6EMGsOyPsjlbBt++Iv7OTh0ZvViBSy8N+jW0cEVY1G2NpfKM2K\n' +
              'UsPs6WevGOaBZ/Ipa0xngpkFexxjGV//DTKKk0WCSA7KHCe1bRYOXrwn3JmYsSDb\n' +
              'EPmqT2xaOOCMMP8rPIA2ugA7+46IgrZIOKsxRwXJXhynD6gx60VlNzEvVACtNtXW\n' +
              'VlTdMQqA9Fb/ZPq9ijx2W1UqFb4xBSVag0Lrz1enJBEcEPCTrJr7iEYg5nEmF4Ph\n' +
              'yWHZABEBAAGJAiUEGAECAA8FAlUlGs8CGwwFCQPCZwAACgkQ9MvVvWeg8YelFhAA\n' +
              'gPo1by0GoWXQ/CDPFJBeoMfsJWW912kzO9ERWhYLGaZFF9c40jwyye5VlNPPYvIc\n' +
              'dwBYufZP3H5BUbko8tHobqsSn4OONqJq1+QfHRDJEOc2NbjFBH2OM9yGPgAuE5sM\n' +
              'aV5uBFxZtmCrVaS3BmUg1ddkAB7DXZoWn6I0YTYDZ5ShTBjIM1LzFF552pIiG8HV\n' +
              '9zcSMtAAYIt0sAYVcdrlMC6ndeBJlKXSujaRNy2yvLrMqGBcW9KdxXOlMk+oFOaM\n' +
              'nyiYiqX4lgEQevzwhG9cW4HcbhWNrW4EE/qKndvjZapRqNu3BZrhxJ1LnCePgS6A\n' +
              'QWeH1e3AN8wDrTRFsKmirTpvnL5SNxbnfbJj9sCf/1oDFYR3Uhu6hU+6ntEB0DiK\n' +
              '5gRGeVlC5G/39HXxDwaIfngWIeHINI25za8ujn2NMleLDQstVw4Ku8KLOuFiQYrj\n' +
              '0lZ3kRpG4qSri1uBM+JY2YS3xuY70ZQh8P2iXr1aQXIzdIBtss684ins+ktlmRq6\n' +
              'BVYOztLuXzyxvxpotLbkTYWaDvdm81YMD/2IerGEND2TF5uEWSa/xGzjf3IGS3va\n' +
              'iLSjzmFCQC28Mr/sA7y3w5Phf9Jd5JH7pta5X0VvGGIuwaegrj6tGPfBTNlO5wxG\n' +
              'QrR0ZxqlZ0Ff1QXnRjFIc1FDjSQ9LEXw7qZ3VjBFBrY=\n' +
              '=/2N2\n' +
              '-----END PGP PUBLIC KEY BLOCK-----';

describe('receiver first login', function() {
  it('should redirect to /firstlogin upon successful authentication', function(done) {
    browser.get('/#/login');
    element(by.model('loginUsername')).element(by.xpath(".//*[text()='Recipient 1']")).click().then(function() {
      element(by.model('loginPassword')).sendKeys('globaleaks').then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
          utils.waitForUrl('/forcedpasswordchange');
          done();
        });
      });
    });
  });

  it('should be able to change password from the default one', function(done) {
    element(by.model('preferences.old_password')).sendKeys('globaleaks').then(function() {
      element(by.model('preferences.password')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
        element(by.model('preferences.check_password')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
          element(by.css('[data-ng-click="pass_save()"]')).click().then(function() {
            utils.waitForUrl('/receiver/tips');
            done();
          });
        });
      });
    });
  });

  it('should be able to login with the new password', function(done) {
    browser.get('/#/login');
    element(by.model('loginUsername')).element(by.xpath(".//*[text()='Recipient 1']")).click().then(function() {
      element(by.model('loginPassword')).sendKeys('ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#').then(function() {
        element(by.xpath('//button[contains(., "Log in")]')).click().then(function() {
          expect(browser.getLocationAbsUrl()).toContain('/receiver/tips');
          done();
        });
      });
    });
  });

  it('should be able to navigate through receiver preferences', function(done) {
    element(by.id('PreferencesLink')).click().then(function() {
      utils.waitForUrl('/receiver/preferences');
      element(by.cssContainingText("a", "General preferences")).click();
      element(by.cssContainingText("a", "Password configuration")).click();
      element(by.cssContainingText("a", "Notification settings")).click();
      element(by.cssContainingText("a", "Encryption settings")).click();
      done();
    });
  });

  it('should be able to load his/her public PGP key', function(done) {
    browser.setLocation('receiver/preferences');
    element(by.cssContainingText("a", "Encryption settings")).click();
    element(by.model('preferences.pgp_key_public')).sendKeys(pgp_key);
    element(by.cssContainingText("span", "Update notification and encryption settings")).click();
    done();
  });
});
