var utils = require('./utils.js');

describe('admin add, configure, and delete users', function() {
  var new_users = [
    {
      role: "Recipient",
      name: "Recipient2",
      address: "globaleaks-receiver2@mailinator.com",
    },
    {
      role: "Recipient",
      name: "Recipient3",
      address: "globaleaks-receiver3@mailinator.com",
    },
    {
      role: "Recipient",
      name: "Recipient4",
      address: "globaleaks-receiver4@mailinator.com",
    },
    {
      role: "Recipient",
      name: "Recipient5",
      address: "globaleaks-receiver5@mailinator.com",
    },
    {
      role: "Custodian",
      name: "Custodian1",
      address: "globaleaks-custodian@mailinator.com",
    },
  ];

  it('should add new users', function() {
    browser.setLocation('admin/users');

    var make_account = function(user) {
      element(by.model('new_user.name')).sendKeys(user.name);
      element(by.model('new_user.email')).sendKeys(user.address);

      if (user.role !== 'Recipient') {
        element(by.model('new_user.username')).sendKeys(user.name);
      }

      element(by.model('new_user.role')).element(by.xpath(".//*[text()='" + user.role + "']")).click();
      element(by.id('add-button')).click();
      utils.waitUntilReady(element(by.xpath(".//*[text()='" + user.name + "']")));
    };

    new_users.forEach(make_account);
  });

  it('should configure an existing user', function() {
    var user = { name: 'Recipient2' };
    var path = '//form[contains(.,"' + user.name + '")]';

    // Find Recipient2, click edit, flip some toggles, and save.
    var editUsrForm = element(by.xpath(path));
    editUsrForm.element(by.css('.actionButtonEdit')).click();
    
    // Pick Alaskan time zone for Giovanni
    var tz = "(GMT -9:00) Alaska";
    var tzBox = editUsrForm.element(by.cssContainingText('option', tz));
    tzBox.click();
    
    // Add a description 
    var descriptBox = editUsrForm.element(by.model('user.description'));
    var words = "Description of recipient 2";
    descriptBox.clear();
    descriptBox.sendKeys(words);

    element(by.model('user.password')).sendKeys(utils.vars['user_password']);
    element(by.model('user.password_change_needed')).click();
    
    // Click Save and check the fields
    editUsrForm.element(by.css('.actionButtonSave')).click();
    editUsrForm.element(by.css('.actionButtonEdit')).click();
    editUsrForm.evaluate('user').then(function(userObj) {
        expect(userObj.timezone).toEqual(-9);
    });
    descriptBox.getAttribute('value').then(function(savedDescript) {
        expect(savedDescript).toEqual(words);
    });
  });

  it('should del existing users', function() {
    // delete's all accounts that match {{ user.name }} for all new_users
    var delete_account = function(user) {
      var path = '//form[contains(.,"' + user.name + '")]';
      element.all(by.xpath(path)).each(function(div) {
        div.element(by.css('.actionButtonDelete')).click();
        element(by.id('modal-action-ok')).click();
      });
    };

    delete_account(new_users[2]);
    delete_account(new_users[3]);
  });
});
