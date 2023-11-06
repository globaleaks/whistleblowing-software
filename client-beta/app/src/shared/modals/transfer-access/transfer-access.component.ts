import {Component, Input} from "@angular/core";
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";

@Component({
  selector: "src-transfer-access",
  templateUrl: "./transfer-access.component.html",
})
export class TransferAccessComponent {
  @Input() usersNames: any;
  @Input() selectableRecipients: any;
  receiverId: string;


  constructor(private activeModal: NgbActiveModal) {
  }

  confirm(receiverId: any) {
    this.activeModal.close(receiverId.id);
  }

  cancel() {
    return this.activeModal.close();
  }
}
