import {Component} from "@angular/core";
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";

@Component({
  selector: "src-enable-encryption",
  templateUrl: "./enable-encryption.component.html"
})
export class EnableEncryptionComponent {
  constructor(protected activeModal: NgbActiveModal) {
  }

  confirm() {
    this.activeModal.close();
  }

  cancel() {
    return this.activeModal.close();
  }
}
