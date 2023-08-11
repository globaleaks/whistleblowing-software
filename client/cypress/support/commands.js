import '@cypress/code-coverage/support';
import 'cypress-file-upload';
Cypress.Commands.add("vars", () => {
  return {
    init_password: "Password12345#",
    field_types: [
      "Single-line text input",
      "Multi-line text input",
      "Selection box",
      "Multiple choice input",
      "Checkbox",
      "Attachment",
      "Terms of service",
      "Date",
      "Date range",
      "Voice",
      "Group of questions",
    ],
  };
});

Cypress.Commands.add("takeScreenshot", (filename, locator) => {
  if (!Cypress.env('takeScreenshots')) {
    return;
  }

  cy.document().then((doc) => {
    const height = doc.body.scrollHeight;
    cy.viewport(1280, height);
  });

  cy.screenshot(filename,{
    overwrite: true
  });
});

Cypress.Commands.add("waitForUrl", (url, timeout) => {
  const t = timeout === undefined ? Cypress.config().defaultCommandTimeout : timeout;
  return cy.url().should("include", url, { timeout: t });
});

Cypress.Commands.add("login_admin", (username, password, url, firstlogin) => {
  username = username === undefined ? "admin" : username;
  password = password === undefined ? Cypress.env("user_password") : password;
  url = url === undefined ? "login" : url;

  let finalURL = "";

  cy.visit(url);

  cy.get('[name="username"]').type(username);
  cy.get('[name="password"]').type(password);
  cy.get("#login-button").click();

  if (firstlogin) {
    finalURL = "/actions/forcedpasswordchange";
    cy.waitForUrl(finalURL);
  } else {
    cy.url().should("include", "/login").then(() => {
      cy.url().should("not.include", "/login").then((currentURL) => {
        const hashPart = currentURL.split("#")[1];
        finalURL = hashPart === "login" ? "/admin/home" : hashPart;
        cy.waitForUrl(finalURL);
      });
    });
  }
});

Cypress.Commands.add("login_receiver", (username, password, url, firstlogin) => {
  username = username === undefined ? "Recipient" : username;
  password = password === undefined ? Cypress.env("user_password") : password;
  url = url === undefined ? "/login" : url;

  cy.visit(url);
  cy.get('[data-ng-model="Authentication.loginData.loginUsername"]').type(username);
  cy.get('[data-ng-model="Authentication.loginData.loginPassword"]').type(password);
  cy.get("#login-button").click();

  if (firstlogin) {
    url = "/actions/forcedpasswordchange";
  } else {
    url = cy.url().then((currentURL) => {
      return currentURL === "/login" ? "/recipient/home" : currentURL;
    });
  }
});

Cypress.Commands.add("login_custodian", (username, password, url, firstlogin) => {
  username = username === undefined ? "Custodian" : username;
  password = password === undefined ? Cypress.env("user_password") : password;
  url = url === undefined ? "/login" : url;

  cy.visit(url);
  cy.get('[data-ng-model="Authentication.loginData.loginUsername"]').type(username);
  cy.get('[data-ng-model="Authentication.loginData.loginPassword"]').type(password);
  cy.get("#login-button").click();

  if (firstlogin) {
    url = "/actions/forcedpasswordchange";
  } else {
    url = cy.url().then((currentURL) => {
      return currentURL === "/login" ? "/recipient/home" : currentURL;
    });
  }
});

Cypress.Commands.add("waitForLoader", () => {
  cy.get('#PageOverlay').should('not.have.class', 'ng-hide');
  cy.get('#PageOverlay.ng-hide');
});

Cypress.Commands.add("logout", () => {
  cy.waitUntilClickable("#LogoutLink");
});

Cypress.Commands.add("makeTestFilePath", (name) => {
  return cy.wrap(Cypress.config("testFiles") + "/files/" + name);
});

Cypress.Commands.add("readExternalFile", (filePath) => {
  return cy.readFile(filePath, "binary");
});

Cypress.Commands.add("waitUntilClickable", (locator, timeout) => {
  const t = timeout === undefined ? Cypress.config().defaultCommandTimeout : timeout;
  return cy.get(locator).click({ timeout: t });
});

Cypress.Commands.add("login_whistleblower", (receipt) => {
  cy.visit("/");

  cy.get('[data-ng-model="formatted_receipt"]').type(receipt);
  cy.screenshot("whistleblower/access.png");
  cy.get("#ReceiptButton").click();
  cy.waitUntilPresent("#TipInfoBox");
});

Cypress.Commands.add("waitUntilPresent", (locator, timeout) => {
  const t = timeout === undefined ? Cypress.config().defaultCommandTimeout : timeout;
  return cy.get(locator).should("be.visible", { timeout: t });
});
