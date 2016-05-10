var utils = require('./utils.js');
var pages = require('./pages.js');

describe('admin add, configure, and delete users', function() {
  var adminLog = new pages.adminLoginPage();
  var new_users = [
    {
      role: "Recipient",
      name: "Recipient 2", 
      address: "globaleaks-receiver2@mailinator.com",
    },
    {
      role: "Recipient",
      name: "Recipient 3", 
      address: "globaleaks-receiver3@mailinator.com",
    },
    {
      role: "Recipient",
      name: "Recipient 4",
      address: "globaleaks-receiver4@mailinator.com",
    },
    {
      role: "Recipient",
      name: "Recipient 5",
      address: "globaleaks-receiver5@mailinator.com",
    },
    {
      role: "Custodian",
      name: "Custodian 1", 
      address: "globaleaks-custodian1@mailinator.com",
    },
  ];

  beforeAll(function() {
    adminLog.login('admin', 'ACollectionOfDiplomaticHistorySince_1966_ToThe_Pr esentDay#');
    browser.setLocation('admin/users');
  });

  it('should add new users', function() {
    var make_account = function(user) {
      element(by.model('new_user.name')).sendKeys(user.name);
      element(by.model('new_user.email')).sendKeys(user.address);

      if (user.role !== 'Recipient') {
        element(by.model('new_user.username')).sendKeys(user.address);
      }

      element(by.model('new_user.role')).element(by.xpath(".//*[text()='" + user.role + "']")).click();
      element(by.css('[data-ng-click="add_user()"]')).click();
      utils.waitUntilReady(element(by.xpath(".//*[text()='" + user.name + "']")));
    };

    new_users.forEach(make_account);
  });

  it('should configure an existing user', function() {
    var user = { name: 'Recipient 1' };
    var path = '//form[contains(.,"' + user.name + '")]';

    // Find Recipient 1, click edit, flip some toggles, and save.
    var editUsrForm = element(by.xpath(path));
    editUsrForm.element(by.css('.actionButtonEdit')).click();
    
    // Pick Alaskan time zone for Giovanni
    var tz = "(GMT -9:00) Alaska";
    var tzBox = editUsrForm.element(by.cssContainingText('option', tz));
    tzBox.click();
    
    // Add a description 
    var descriptBox = editUsrForm.element(by.model('user.description'));
    var words = "Description of recipient 1";
    descriptBox.clear();
    descriptBox.sendKeys(words);
    
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
