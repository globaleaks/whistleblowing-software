describe("admin add, configure, and delete users", function() {
  var new_users = [
    {
      role: "Recipient",
      name: "Recipient1",
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
      name: "Custodian1",
      address: "globaleaks-custodian@mailinator.com",
    },
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
      await browser.gl.utils.waitUntilPresent(by.xpath(".//*[text()='" + user.name + "']"));
    };

    for(var i=0; i < new_users.length; i++) {
      await make_account(new_users[i]);
    }
  });

  it("should configure an Recipient 1", async function() {
    var user = { name: "Recipient1" };
    var path = "//form[contains(.,\"" + user.name + "\")]";

    // Find Recipient2, click edit, flip some toggles, and save.
    var editUsrForm = element(by.xpath(path));

    await editUsrForm.element(by.cssContainingText("button", "Edit")).click();

    // Add a description
    var descriptBox = editUsrForm.element(by.model("user.description"));
    var words = "Description of recipient 1";
    await descriptBox.clear();
    await descriptBox.sendKeys(words);

    await editUsrForm.all(by.cssContainingText("span", "Set password")).first().click();
    await element(by.model("user.password")).sendKeys("globaleaks123!");

    // Click Save and check the fields
    await editUsrForm.element(by.cssContainingText("button", "Save")).click();
    await editUsrForm.element(by.cssContainingText("button", "Edit")).click();

    expect(await descriptBox.getAttribute("value")).toEqual(words);
  });

  it("should configure an Recipient 2", async function() {
    var user = { name: "Recipient2" };
    var path = "//form[contains(.,\"" + user.name + "\")]";

    // Find Recipient2, click edit, flip some toggles, and save.
    var editUsrForm = element(by.xpath(path));

    await editUsrForm.element(by.cssContainingText("button", "Edit")).click();

    await editUsrForm.all(by.cssContainingText("span", "Set password")).first().click();
    await element(by.model("user.password")).sendKeys("globaleaks123!");

    // Click Save and check the fields
    await editUsrForm.element(by.cssContainingText("button", "Save")).click();
  });

  it("should configure an Custodian 1", async function() {
    var user = { name: "Custodian1" };
    var path = "//form[contains(.,\"" + user.name + "\")]";

    // Find Recipient2, click edit, flip some toggles, and save.
    var editUsrForm = element(by.xpath(path));

    await editUsrForm.element(by.cssContainingText("button", "Edit")).click();

    await editUsrForm.all(by.cssContainingText("span", "Set password")).first().click();
    await element(by.model("user.password")).sendKeys("globaleaks123!");

    // Click Save and check the fields
    await editUsrForm.element(by.cssContainingText("button", "Save")).click();
  });

  it("should del existing users", async function() {
    // delete's all accounts that match {{ user.name }} for all new_users
    var delete_account = async function(user) {
      var path = "//form[contains(.,\"" + user.name + "\")]";
      var elements = element.all(by.xpath(path));
      for (var i=0; i<elements.length; i++) {
        await elements[i].element(by.cssContainingText("button", "Delete")).click();
        await element(by.id("modal-action-ok")).click();
      }
    };

    await delete_account(new_users[2]);
    await delete_account(new_users[3]);
  });
});
