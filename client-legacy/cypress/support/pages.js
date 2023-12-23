class ReceiverPage {
  viewMostRecentSubmission() {
    cy.get("#tip-0").click();
  }

  wbfileWidget() {
    return cy.get("#TipPageWBFileUpload");
  }

  uploadWBFile(fname) {
    cy.get("input[type='file']").selectFile(fname);
  }
}

class WhistleblowerPage {
  performSubmission() {
    cy.visit("/");
    cy.takeScreenshot("whistleblower/home");

    cy.get("#WhistleblowingButton").click();
    cy.get("#SubmissionForm").should("be.visible");

    cy.get("#step-0-field-0-0-input-0").type("summary");
    cy.get("#step-0-field-1-0-input-0").type("detail");
    cy.get("#step-0-field-2-0-input-0").type("...");
    cy.get("#step-0-field-2-1-input-0").type("...");


    cy.get("#step-0-field-3-0-input-0").first().select("13d17a19-1c7c-482c-9e6c-16896f0d5f1b");
    cy.get("#step-0-field-4-0-input-0").first().select("Yes");

    cy.get("#step-0-field-6-0-input-0").type("...");

    cy.get("#step-0-field-5-0-input-0 input[type='file']").selectFile({
      contents: "./cypress/fixtures/files/evidence-1.pdf",
      fileName: "evidence-1.pdf",
      mimeType: "application/pdf"
    }, {"force": true});

    cy.get("#step-0-field-5-0-input-0 input[type='file']").selectFile({
      contents: "./cypress/fixtures/files/evidence-2.zip",
      fileName: "evidence-2.zip",
      mimeType: "application/zip"
    }, {"force": true});

    cy.get("#step-0-field-7-0-input-0").first().select("No");

    cy.get("#step-0-field-10-0-input-0").type("...");
    cy.wait(1000)
    cy.get("#SubmitButton").should("be.visible");

    cy.takeScreenshot("whistleblower/submission");

    cy.get("#SubmitButton").click();

    cy.wait(1000);

    cy.get("#ReceiptCode").should("be.visible");

    cy.takeScreenshot("whistleblower/receipt");

    return cy.get('#ReceiptCode').invoke('val').then((value) => {
      return value;
    });
  }

  submitFile(fname) {
    cy.get("input[type='file']").selectFile(fname, {"force": true});
  }
}

module.exports = {
  receiver: new ReceiverPage(),
  whistleblower: new WhistleblowerPage()
};
