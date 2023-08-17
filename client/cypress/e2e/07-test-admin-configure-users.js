describe("admin add, configure, and delete users", () => {
  const new_users = [
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

  it("should add new users", () => {
    cy.login_admin();
    cy.visit("/#/admin/users");

    const make_account = (user) => {
      cy.get(".show-add-user-btn").click();
      cy.get("[data-ng-model='new_user.role']").select(user.role);
      cy.get("[data-ng-model='new_user.username']").clear().type(user.name);
      cy.get("[data-ng-model='new_user.name']").clear().type(user.name);
      cy.get("[data-ng-model='new_user.email']").clear().type(user.address);
      cy.get("#add-btn").click();
      cy.waitForLoader();
    };

    for (let i = 0; i < new_users.length; i++) {
      make_account(new_users[i]);
      cy.get(".userList").should('have.length', i + 2);
    }
  });

  it("should grant permissions to the first recipient", () => {
    cy.login_admin();
    cy.visit("/#/admin/users");

    cy.get(".userList").eq(3).within(() => {
      cy.contains("button", "Edit").click();
      cy.get("[data-ng-model='user.can_delete_submission']").click();
      cy.contains("button", "Save").click();
    });
  });

  it("should configure users' passwords", () => {
    cy.login_admin();
    cy.visit("/#/admin/users");

    cy.get(".userList").its("length").then(userListLength => {
      const numberOfUsers = Math.min(userListLength, 6);
      for (let i = 1; i < numberOfUsers; i++) {
        cy.get(".userList").eq(i).within(() => {
          if (Cypress.$("button:contains('Edit')").length > 0) {
            cy.contains("button", "Edit").click();
            cy.contains("span", "Set password").first().click();
            cy.get("[data-ng-model='setPasswordArgs.password']").clear().type(Cypress.env("init_password"));
            cy.get("#setPasswordButton").first().click();
          }
        });
      }
    });

    cy.logout();
  });

});
