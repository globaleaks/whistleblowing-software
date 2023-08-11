import pages from '../support/pages'; // Adjust the path as needed

describe("globaleaks process", function () {
  const N = 1;
  let receipts = [];
  const comment = "comment";
  const comment_reply = "comment reply";

  const perform_submission = async () => {
    const wbPage = pages.whistleblower;

    wbPage.performSubmission(true).then((receipt) => {
      receipts.unshift(receipt);
    });
  };

  for (let i = 1; i <= N; i++) {
    it("Whistleblowers should be able to perform a submission", function () {
      perform_submission();
    });
    it("Recipient should be able to access, label and mark as important the last submission", function () {
      cy.login_receiver();
      cy.waitForUrl("/recipient/home")
      cy.visit("/recipient/reports");

      cy.get("#tip-0").first().click();

      cy.get(".TipInfoID").invoke("text").then((id) => {
        const cleanId = id.trim();

        cy.contains("summary").should("exist");

        cy.get("[data-ng-model='tip.label']").type("Important");
        cy.get("#assignLabelButton").click();

        cy.get("#tip-action-star").click();
      });
    });

    it("Recipient should be able to see files and download them", function () {
      cy.get(".tip-action-download-file").should("have.length", 2);
      cy.get(".tip-action-download-file").eq(0).click();
    });

    it("Recipient should be able to leave a comment to the whistleblower", function () {
      const comment = "comment";

      cy.get("[data-ng-model='tip.newCommentContent']").type(comment);
      cy.get("#comment-action-send").click();

      cy.get("#comment-0 .preformatted").should("contain", comment);

      cy.visit("/recipient/reports");
      cy.screenshot("recipient/reports.png");

      cy.logout();
    });

    it("Whistleblower should be able to read the comment from the receiver and reply", function () {
      const comment_reply = "comment reply"; // Replace with your comment reply text

      cy.login_whistleblower(receipts[0]);

      cy.get("#comment-0 .preformatted").should("contain", comment);

      cy.get("[data-ng-model='tip.newCommentContent']").type(comment_reply);
      cy.get("#comment-action-send").click();

      cy.get("#comment-0 .preformatted").should("contain", comment_reply);

      cy.screenshot("whistleblower/report.png");
    });

    it("Whistleblower should be able to attach a new file to the last submission", function() {
      cy.fixture("files/evidence-3.txt").then(fileContent => {

        cy.get('input[type="file"]').then(input => {
          const blob = new Blob([fileContent], { type: "text/plain" });
          const testFile = new File([blob], "files/evidence-3.txt");
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(testFile);
          input[0].files = dataTransfer.files;

          const changeEvent = new Event("change", { bubbles: true });
          input[0].dispatchEvent(changeEvent);
        });

        cy.get("#files-action-confirm").click();
        cy.get(".progress-bar-complete", { timeout: 10000 }).should("exist");
      });
    });

    it("Recipient should be able to export the submission", function() {
      cy.login_receiver();
      cy.waitForLoader();

      cy.visit("/recipient/reports");
      cy.get("#tip-0").first().click();
      cy.waitForLoader();
      cy.get('#tip-action-export').invoke('click');
      cy.wait(500)
      cy.get(".TipInfoID").first().invoke("text").then(t => {
        expect(t.trim()).to.be.a("string");
      });
      cy.logout();
    });
    it("Recipient should be able to disable and re-enable email notifications", () => {
      cy.login_receiver();
      cy.waitForLoader();
      cy.visit("/recipient/reports");

      cy.get("#tip-0").first().click();
      cy.waitForLoader();

      cy.get('[id="tip-action-silence"]').click();

      cy.get('[id="tip-action-notify"]').invoke("attr", "data-ng-if").then((attrValue) => {
        const isEnabled = attrValue === "!tip.enable_notifications";
        expect(isEnabled).to.be.true;

        cy.get('[id="tip-action-notify"]').click();

        cy.get('[id="tip-action-silence"]').invoke("attr", "data-ng-if").then((attrValueAfter) => {
          const isEnabledAfter = attrValueAfter === "!tip.enable_notifications";
          expect(isEnabledAfter).to.be.false;

          cy.takeScreenshot("recipient/report.png");
          cy.logout();
        });
      });
    });
  }
});
