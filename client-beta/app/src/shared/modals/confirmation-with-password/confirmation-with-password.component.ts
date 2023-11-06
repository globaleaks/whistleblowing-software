import {Component} from "@angular/core";
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";

@Component({
  selector: "src-confirmation-with-password",
  templateUrl: "./confirmation-with-password.component.html"
})
export class ConfirmationWithPasswordComponent {
  secretModel: any;

  constructor(private activeModal: NgbActiveModal) {
  }

  confirmFunction: (secret: string) => void;

  dismiss() {
    this.activeModal.dismiss();
  }

  confirm() {
    this.confirmFunction(this.secretModel);
    return this.activeModal.close(this.secretModel);
  }
}
