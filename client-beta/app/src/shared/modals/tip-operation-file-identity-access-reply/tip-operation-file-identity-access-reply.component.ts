import {Component, Input} from "@angular/core";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-tip-operation-file-identity-access-reply",
  templateUrl: "./tip-operation-file-identity-access-reply.component.html"
})
export class TipOperationFileIdentityAccessReplyComponent {

  reply_motivation = "";
  @Input() iar_id = "";

  constructor(private httpService: HttpService, private modalService: NgbModal, private utilsService: UtilsService) {
  }

  cancel() {
    this.modalService.dismissAll();
  }

  confirm() {
    this.httpService.authorizeIdentity("api/custodian/iars/" + this.iar_id, {
      "reply": "denied",
      "reply_motivation": this.reply_motivation
    }).subscribe(
      {
        next: () => {
          this.utilsService.reloadCurrentRoute();
        }
      }
    );
    this.cancel();
  }
}
