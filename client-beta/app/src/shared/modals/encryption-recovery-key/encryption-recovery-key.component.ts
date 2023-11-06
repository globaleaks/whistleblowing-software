import {Component, Input} from "@angular/core";
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-encryption-recovery-key",
  templateUrl: "./encryption-recovery-key.component.html"
})
export class EncryptionRecoveryKeyComponent {

  @Input() erk: any;

  constructor(private activeModal: NgbActiveModal, protected utilsService: UtilsService) {
  }

  dismiss() {
    this.activeModal.dismiss();
  }
}
