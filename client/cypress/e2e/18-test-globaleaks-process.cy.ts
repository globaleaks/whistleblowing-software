import * as pages from '../support/pages';

describe("globaleaks process", function () {
  const N = 1;
  let receipts:any = [];
  const comment = "comment";

  const perform_submission = async () => {
    const wbPage = pages.WhistleblowerPage;

    wbPage.performSubmission().then((receipt) => {
      receipts.unshift(receipt);
    });
  };

  for (let i = 1; i <= N; i++) {
    it("Whistleblowers should be able to perform a submission", function () {
      perform_submission();
    });

    it("Recipient actions ", function () {
      /* file upload delay */
      cy.wait(3000)
      cy.login_receiver();
      cy.waitForUrl("/#/recipient/home");
      cy.visit("/#/recipient/reports");

      cy.get("#tip-0").should('be.visible', { timeout: 10000 }).first().click();

      cy.get(".TipInfoID").invoke("text").then((_) => {
        cy.contains("summary").should("exist");

        cy.get("[name='tip.label']").type("Important");
        cy.get("#assignLabelButton").click();

        cy.get("#tip-action-star").click();
      });

      cy.get('#fileListBody', { timeout: 10000 }).find('tr').should('have.length', 2);

      const comment = "comment";
      cy.get("[name='newCommentContent']").type(comment);
      cy.get("#comment-action-send").click();
      cy.waitForLoader();
      cy.get('#comment-0').should('contain', comment);
      cy.visit("/#/recipient/reports");
      cy.takeScreenshot("recipient/reports", 0);

      cy.logout();
    });

    it("Whistleblower actions", function () {
      const comment_reply = "comment reply";

      cy.login_whistleblower(receipts[0]);

      cy.get("#comment-0").should("contain", comment);

      cy.get("[name='newCommentContent']").type(comment_reply);
      cy.get("#comment-action-send").click();

      cy.get("#comment-0 .preformatted").should("contain", comment_reply);

      cy.takeScreenshot("whistleblower/report", 0);

      cy.fixture("files/evidence-3.txt").then(fileContent => {
        cy.get('input[type="file"]').then(input => {
          const blob = new Blob([fileContent], { type: "text/plain" });
          const testFile = new File([blob], "files/evidence-3.txt");
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(testFile);
          const inputElement = input[0] as HTMLInputElement;
          inputElement.files = dataTransfer.files;

          const changeEvent = new Event("change", { bubbles: true });
          input[0].dispatchEvent(changeEvent);
        });

        cy.get("#files-action-confirm").click();
        // cy.get(".progress-bar-complete", { timeout: 10000 }).should("be.visible");
      });

      cy.logout();
    });

    it("Recipient actions", function() {
      cy.login_receiver();
      cy.visit("/#/recipient/reports");

      cy.get("#tip-0").first().click();
      cy.get('#tip-action-export').invoke('click');
      cy.get(".TipInfoID").first().invoke("text").then(t => {
        expect(t.trim()).to.be.a("string");
      });
      cy.waitForLoader();
      cy.get('[id="tip-action-silence"]').should('be.visible', { timeout: 10000 }).click();
      cy.get('#tip-action-notify').should('be.visible', { timeout: 10000 }).click();
      cy.get('#tip-action-silence').should('be.visible', { timeout: 10000 }).should('be.visible');
      cy.takeScreenshot("recipient/report", 0);

      cy.logout();
    });
  }
});
