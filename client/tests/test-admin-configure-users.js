describe("admin add, configure, and delete users", function() {
  var new_users = [
    {
      role: "Recipient",
      name: "Recipient",
      address: "globaleaks-receiver1@mailinator.com",
    },
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
      role: "Custodian",
      name: "Custodian",
      address: "globaleaks-custodian1@mailinator.com",
    },
    {
      role: "Admin",
      name: "Admin2",
      address: "globaleaks-admin2@mailinator.com",
    }
  ];

  it("should add new users", async function() {
    await browser.gl.utils.login_admin();
    await browser.setLocation("admin/users");

    var make_account = async function(user) {
      await element(by.css(".show-add-user-btn")).click();
      await element(by.model("new_user.name")).sendKeys(user.name);
      await element(by.model("new_user.email")).sendKeys(user.address);
      await element(by.model("new_user.username")).sendKeys(user.name);
      await element(by.model("new_user.role")).element(by.xpath(".//*[text()='" + user.role + "']")).click();
      await element(by.id("add-btn")).click();
    };

    for(var i=0; i < new_users.length; i++) {
      await make_account(new_users[i]);
    }
  });

  it("should grant permissions to recipientson first recipient", async function() {
    await element.all(by.className("userList")).then(async function(elements) {
      var editUsrForm = elements[3];
      await editUsrForm.element(by.cssContainingText("button", "Edit")).click();
      await element(by.model("user.can_delete_submission")).click();
      await element(by.model("user.can_postpone_expiration")).click();
      await editUsrForm.element(by.cssContainingText("button", "Save")).click();
    });
  });

  it("should configure users' passwords", async function() {
    for (var i = 1; i < 6; i++) {
      await browser.setLocation("admin/users");
      await element.all(by.className("userList")).then(async function(elements) {
	var editUsrForm = elements[i];
        await editUsrForm.element(by.cssContainingText("button", "Edit")).click();
        await editUsrForm.all(by.cssContainingText("span", "Set password")).first().click();
        await element(by.model("user.password")).sendKeys("Globaleaks123!");
        await editUsrForm.element(by.cssContainingText("button", "Save")).click();
      });
    }
  });
});
