describe('globaLeaks setup receiver(s)', function() {
  it('should allow the user to setup the wizard', function() {

      var usernames = [
          "Receiver0",
          "Receiver1",
          "Receiver2",
          "Receiver3",
          "Receiver4",
          "Receiver5"
      ];
      for (var i = 0, len = usernames.length; i < len; i++ ) {

        console.log("   " + i + " = " + usernames[i]);
        browser.get('http://127.0.0.1:8082/login');
        browser.sleep(500);

        element(by.cssContainingText('option', usernames[i])).click();

        element(by.model('loginPassword')).sendKeys('globaleaks');
        element(by.css('button')).click();

        // new page, change password for the first time (and create PGP key)
        element(by.model('preferences.old_password')).sendKeys('globaleaks');
        element(by.model('preferences.password')).sendKeys('Antani1234');
        element(by.model('preferences.check_password')).sendKeys('Antani1234');

        element(by.id('CreateKeyButton')).click();
        // expect(browser.getLocation().isToBe('#/receivers/tips'));
        for (var s = 0; s < 10; s++) {
          console.log(s + " sleep...");
          browser.sleep(1000);
        }
        element(by.id('LogoutButton')).click();
        browser.sleep(1500);
      }
   });
});
