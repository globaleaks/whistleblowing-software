class ReceiverPage {
  viewMostRecentSubmission() {
    cy.get("#tip-0").click();
  }

  addPublicKey(pgp_key_path) {
    cy.visit("/recipient/preferences");
    cy.get("input[type='file']").attachFile(pgp_key_path);
    cy.contains("span", "Save").first().click();
  }

  wbfileWidget() {
    return cy.get("#TipPageWBFileUpload");
  }

  uploadWBFile(fname) {
    cy.get("input[type='file']").attachFile(fname);
  }
}

class WhistleblowerPage {
  performSubmission() {
    cy.visit("/");
    cy.get("#WhistleblowingButton").click();
    cy.get("#SubmissionForm").should("be.visible");

    cy.get("#step-0-field-0-0-input-0").type("summary");
    cy.get("#step-0-field-1-0-input-0").type("detail");
    cy.get("#step-0-field-2-0-input-0").type("...");
    cy.get("#step-0-field-2-1-input-0").type("...");


    cy.get("#step-0-field-3-0-input-0").first().select("13d17a19-1c7c-482c-9e6c-16896f0d5f1b");
    cy.get("#step-0-field-4-0-input-0").first().select("Yes");

    cy.get("#step-0-field-6-0-input-0").type("...");

    const fileToUpload1 = "evidence-1.pdf";
    const fileToUpload2 = "evidence-2.zip";

    cy.get("#step-0-field-5-0-input-0 input[type='file']").attachFile({
      fileContent: fileToUpload1,
      fileName: fileToUpload1,
      mimeType: "application/pdf"
    });

    cy.get("#step-0-field-5-0-input-0 input[type='file']").attachFile({
      fileContent: fileToUpload2,
      fileName: fileToUpload2,
      mimeType: "application/zip"
    });

    cy.get("#step-0-field-7-0-input-0").first().select("No");

    cy.get("#step-0-field-10-0-input-0").type("...");
    cy.wait(1000)
    cy.get("#SubmitButton").should("be.visible").click();
    cy.get("#ReceiptCode").should("be.visible");

    return cy.get('#ReceiptCode').invoke('val').then((value) => {
      // Optionally, you can also log the value
      console.log('Receipt Code:', value);
      return value;
    });
  }

  submitFile(fname) {
    cy.get("input[type='file']").attachFile(fname);
  }
}

module.exports = {
  receiver: new ReceiverPage(),
  whistleblower: new WhistleblowerPage()
};
