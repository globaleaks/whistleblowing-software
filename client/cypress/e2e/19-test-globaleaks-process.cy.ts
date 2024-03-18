import * as pages from '../support/pages';

describe("globaleaks process", function () {
  const N = 1;
  let receipts: any = [];
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

      cy.waitForTipImageUpload();
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
        cy.get('[data-cy="progress-bar-complete"]', { timeout: 10000 }).should("be.visible");
      });

      cy.logout();
    });

    it("Recipient actions", function () {
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
  it("should update default context", () => {
    cy.login_admin();
    cy.visit("/#/admin/contexts");
    cy.get("#edit_context").first().click();
    cy.get('select[name="contextResolver.questionnaire_id"]').select('testing 1');
    cy.get("#advance_context").click();
    cy.get('select[name="contextResolver.additional_questionnaire_id"]').select('testing 2');
    cy.get("#save_context").click();
    cy.logout();
  })
  it("should run audio questionnaire", () => {
    cy.visit("#/");
    cy.get("#WhistleblowingButton").click();
    cy.get("#step-0").should("be.visible");
    cy.get("#step-0-field-0-0-input-0")
    cy.get("#start_recording").click();
    cy.wait(6000);
    cy.get("#stop_recording").click();
    cy.get("#NextStepButton").click();
    cy.get("#SubmitButton").should("be.visible");
    cy.get("#SubmitButton").click();
  })
  it("should run identity , upload file & additional questionnaire", () => {
    cy.visit("#/");
    cy.reload();
    cy.get("#WhistleblowingButton").click();
    cy.get("#NextStepButton").click();
    cy.get("input[type='text']").eq(1).should("be.visible").type("abc");
    cy.get("input[type='text']").eq(2).should("be.visible").type("xyz");
    cy.get("select").first().select(1);
    cy.get("#SubmitButton").should("be.visible");
    cy.get("#SubmitButton").click();
    cy.get('.mt-md-3.clearfix.ng-star-inserted').find('#ReceiptButton').click();
    cy.get("#open_additional_questionnaire").click();
    cy.get("input[type='text']").eq(1).should("be.visible").type("single line text input");
    cy.get("#SubmitButton").click();
    cy.get('i.fa-solid.fa-upload').click();
    cy.fixture("files/dummy-image.jpg").then(fileContent => {
      cy.get('input[type="file"]').then(input => {
        const blob = new Blob([fileContent], { type: "image/jpeg" });
        const testFile = new File([blob], "files/dummy-image.jpg");
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(testFile);
        const inputElement = input[0] as HTMLInputElement;
        inputElement.files = dataTransfer.files;

        const changeEvent = new Event("change", { bubbles: true });
        input[0].dispatchEvent(changeEvent);
      });
    });
    cy.get("#files-action-confirm", { timeout: 10000 }).click();
    cy.logout();
  });
  it("should view the whistleblower file", () => {
    cy.login_receiver();
    cy.reload();
    cy.visit("/#/recipient/reports");
    cy.get("#tip-0").first().click();
    cy.get(".tip-action-views-file", { timeout: 10000 }).first().click();
    cy.get("#modal-action-cancel").click();
    cy.logout();
  })
  it("should request for identity", () => {
    cy.login_receiver();
    cy.visit("/#/recipient/reports");
    cy.get("#tip-0").first().click();
    cy.get('[data-cy="identity_toggle"]').click();
    cy.get("#identity_access_request").click();
    cy.get('textarea[name="request_motivation"]').type("This is the motivation text.");
    cy.get('#modal-action-ok').click();
    cy.logout();
  })
  it("should deny authorize identity", () => {
    cy.login_custodian();
    cy.get("#custodian_requests").first().click();
    cy.get("#deny").first().click();
    cy.get('#motivation').type("This is the motivation text.");
    cy.get('#modal-action-ok').click();
    cy.logout();
  })
  it("should request for identity", () => {
    cy.login_receiver();
    cy.visit("/#/recipient/reports");
    cy.get("#tip-0").first().click();
    cy.get('[data-cy="identity_toggle"]').click();
    cy.get("#identity_access_request").click();
    cy.get('textarea[name="request_motivation"]').type("This is the motivation text.");
    cy.get('#modal-action-ok').click();
    cy.logout();
  })
  it("should authorize identity", () => {
    cy.login_custodian();
    cy.get("#custodian_requests").first().click();
    cy.get("#authorize").first().click();
    cy.logout();
  })
  it("should revert default context", () => {
    cy.login_admin();
    cy.visit("/#/admin/contexts");
    cy.get("#edit_context").first().click();
    cy.get('select[name="contextResolver.questionnaire_id"]').select('GLOBALEAKS');
    cy.get("#save_context").click();
    cy.logout();
  });
  it("should mask reported data", function () {
    cy.login_receiver();
    cy.visit("/#/recipient/reports");
    cy.get("#tip-0").first().click();
    cy.get('[id="tip-action-mask"]').should('be.visible', { timeout: 10000 }).click();
    cy.get("#edit-question").should('be.visible').first().click();

    cy.get('textarea[name="controlElement"]').should('be.visible').then((textarea: any) => {
      const val = textarea.val();
      cy.get('textarea[name="controlElement"]').should('be.visible').clear().type(val);
      cy.get("#select_content").click();
      cy.wait(1000);
    });
    cy.get("#save_masking").click();
    cy.get('[id="tip-action-mask"]').should('be.visible', { timeout: 10000 }).click();
    cy.get("#edit-question").should('be.visible').first().click();
    cy.get('textarea[name="controlElement"]').should('be.visible').then((textarea: any) => {
      const val = textarea.val();
      cy.get('textarea[name="controlElement"]').should('be.visible').clear().type(val);
      cy.get("#unselect_content").click();
      cy.wait(1000);
    });
    cy.get("#save_masking").click();
    cy.logout();
  });
});
