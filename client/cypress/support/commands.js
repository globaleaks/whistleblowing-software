import '@cypress/code-coverage/support';
import { PageIdleDetector } from './PageIdleDetector.js';

Cypress.Commands.add("waitForPageIdle", () => {
    const pageIdleDetector = new PageIdleDetector();

    pageIdleDetector.WaitForPageToBeIdle();
  }
);

Cypress.Commands.add("takeScreenshot", (filename, locator) => {
  if (!Cypress.env('takeScreenshots')) {
    return;
  }
  
  cy.get("html, body").invoke(
    "attr",
    "style",
    "height: auto; scroll-behavior: auto;"
  );

  return cy.document().then((doc) => {
    cy.viewport(1280, doc.body.scrollHeight);

    cy.waitForPageIdle();

    cy.screenshot("../" + filename, {
      overwrite: true
    });
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

  let finalURL = "/actions/forcedpasswordchange";

  cy.visit(url);

  cy.get('[name="username"]').type(username);
  cy.get('[name="password"]').type(password);
  cy.get("#login-button").click();

  if (!firstlogin) {
    cy.url().should("include", "/login").then(() => {
      cy.url().should("not.include", "/login").then((currentURL) => {
        const hashPart = currentURL.split("#")[1];
        finalURL = hashPart === "login" ? "/admin/home" : hashPart;
        cy.waitForUrl(finalURL);
      });
    });
  }

  cy.waitForPageIdle();
});

Cypress.Commands.add("login_receiver", (username, password, url, firstlogin) => {
  username = username === undefined ? "Recipient" : username;
  password = password === undefined ? Cypress.env("user_password") : password;
  url = url === undefined ? "/login" : url;

  let finalURL = "/actions/forcedpasswordchange";

  cy.visit(url);
  cy.get('[data-ng-model="Authentication.loginData.loginUsername"]').type(username);
  cy.get('[data-ng-model="Authentication.loginData.loginPassword"]').type(password);
  cy.get("#login-button").click();

  if (!firstlogin) {
    cy.url().should("include", "/login").then(() => {
      cy.url().should("not.include", "/login").then((currentURL) => {
        const hashPart = currentURL.split("#")[1];
        finalURL = hashPart === "login" ? "/recipient/home" : hashPart;
        cy.waitForUrl(finalURL);
      });
    });
  }

  cy.waitForPageIdle();
});

Cypress.Commands.add("login_custodian", (username, password, url, firstlogin) => {
  username = username === undefined ? "Custodian" : username;
  password = password === undefined ? Cypress.env("user_password") : password;
  url = url === undefined ? "/login" : url;

  let finalURL = "/actions/forcedpasswordchange";

  cy.visit(url);
  cy.get('[data-ng-model="Authentication.loginData.loginUsername"]').type(username);
  cy.get('[data-ng-model="Authentication.loginData.loginPassword"]').type(password);
  cy.get("#login-button").click();

  if (!firstlogin) {
    cy.url().should("include", "/login").then(() => {
      cy.url().should("not.include", "/login").then((currentURL) => {
        const hashPart = currentURL.split("#")[1];
        finalURL = hashPart === "login" ? "/custodian/home" : hashPart;
        cy.waitForUrl(finalURL);
      });
    });
  }

  cy.waitForPageIdle();
});

Cypress.Commands.add("waitForLoader", () => {
  return cy.get('#PageOverlay').should('not.be.visible');
});

Cypress.Commands.add("logout", () => {
  cy.get("#LogoutLink").click();
  cy.get("#LogoutLink").should("not.exist");
});

Cypress.Commands.add("makeTestFilePath", (name) => {
  return cy.wrap(Cypress.config("testFiles") + "/files/" + name);
});

Cypress.Commands.add("readExternalFile", (filePath) => {
  return cy.readFile(filePath, "binary");
});

Cypress.Commands.add("login_whistleblower", (receipt) => {
  cy.visit("/");

  cy.get('[data-ng-model="formatted_receipt"]').type(receipt);
  cy.get("#ReceiptButton").click();
  cy.get("#ReceiptButton").should("not.exist");
});

Cypress.Commands.overwrite('visit', (originalFn, url, options) => {
  cy.waitForPageIdle();
  originalFn(url, options);
  cy.waitForPageIdle();
  cy.waitForLoader();
});
