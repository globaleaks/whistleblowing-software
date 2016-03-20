var utils = require('./utils.js');

describe('admin add users', function() {
  it('should add new users', function(done) {
    browser.setLocation('admin/users');

    var add_user = function(role, roleSelector, name, address) {
      return protractor.promise.controlFlow().execute(function() {
        var deferred = protractor.promise.defer();
        element(by.model('new_user.name')).sendKeys(name);
        element(by.model('new_user.email')).sendKeys(address);
        element(by.model('new_user.role')).element(by.xpath(".//*[text()='" + roleSelector + "']")).click();
        element(by.css('[data-ng-click="add_user()"]')).click().then(function() {
           utils.waitUntilReady(element(by.xpath(".//*[text()='" + name + "']")));
           deferred.fulfill();
        });
        return deferred.promise;
      });
    };

    add_user("receiver", "Recipient", "Recipient 2", "globaleaks-receiver2@mailinator.com");
    add_user("receiver", "Recipient", "Recipient 3", "globaleaks-receiver3@mailinator.com");
    add_user("custodian", "Custodian", "Custodian 1", "globaleaks-custodian1@mailinator.com");
    done();
  });
});
