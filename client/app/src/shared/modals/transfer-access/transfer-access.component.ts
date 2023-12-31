import {Component, Input} from "@angular/core";
import {Receiver} from "@app/models/app/public-model";
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";

@Component({
  selector: "src-transfer-access",
  templateUrl: "./transfer-access.component.html",
})
export class TransferAccessComponent {
  @Input() usersNames: Record<string, string> | undefined;
  @Input() selectableRecipients: Receiver[];
  receiverId: { id: number };

  constructor(private activeModal: NgbActiveModal) {
  }

  confirm(receiverId: { id: number }) {
    this.activeModal.close(receiverId.id);
  }

  cancel() {
    return this.activeModal.close();
  }
}
