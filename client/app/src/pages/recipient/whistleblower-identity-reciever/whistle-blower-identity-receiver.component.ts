import {Component, Input} from "@angular/core";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {ReceiverTipService} from "@app/services/helper/receiver-tip.service";
import {
  TipOperationFileIdentityAccessRequestComponent
} from "@app/shared/modals/tip-operation-file-identity-access-request/tip-operation-file-identity-access-request.ompoent";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";


@Component({
  selector: "src-whistleblower-identity-reciever",
  templateUrl: "./whistle-blower-identity-receiver.component.html"
})
export class WhistleBlowerIdentityReceiverComponent {
  @Input() redactOperationTitle: string;
  @Input() redactMode: boolean;
  collapsed: boolean = true;

  constructor(protected tipService: ReceiverTipService, protected utilsService: UtilsService, private httpService: HttpService, private modalService: NgbModal, private utils: UtilsService) {
  }

  public toggleCollapse() {
    this.collapsed = !this.collapsed;
  }

  fileIdentityAccessRequest() {
    const modalRef = this.modalService.open(TipOperationFileIdentityAccessRequestComponent, {
      backdrop: 'static',
      keyboard: false
    });
    modalRef.componentInstance.tip = this.tipService.tip;
  }

  accessIdentity() {
    return this.httpService.accessIdentity(this.tipService.tip.id).subscribe(
      _ => {
        this.utils.reloadCurrentRoute();
      }
    );
  }
}
