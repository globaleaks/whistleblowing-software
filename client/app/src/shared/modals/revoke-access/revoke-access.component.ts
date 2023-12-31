import {Component, Input} from "@angular/core";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {UtilsService} from "@app/shared/services/utils.service";
import {Receiver} from "@app/models/app/public-model";


@Component({
  selector: "src-revoke-access",
  templateUrl: "./revoke-access.component.html"
})
export class RevokeAccessComponent {


  @Input() usersNames: Record<string, string> | undefined;
  @Input() selectableRecipients: Receiver[];
  @Input() confirmFun: Function;
  @Input() cancelFun: Function;
  receiver_id: { id: number };

  constructor(private modalService: NgbModal, private utils: UtilsService) {
  }

  confirm() {
    this.cancel();
    if (this.confirmFun) {
      this.confirmFun(this.receiver_id);
    }
  }

  reload() {
    this.utils.reloadCurrentRoute();
  }

  cancel() {
    if (this.cancelFun) {
      this.cancelFun();
    }
    this.modalService.dismissAll();
  }
}
