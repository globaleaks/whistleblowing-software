import {Component, Input} from "@angular/core";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {UtilsService} from "@app/shared/services/utils.service";
import {AppDataService} from "@app/app-data.service";


@Component({
  selector: "src-revoke-access",
  templateUrl: "./revoke-access.component.html"
})
export class RevokeAccessComponent {


  @Input() usersNames: any;
  @Input() selectableRecipients: any;
  @Input() confirmFun: Function;
  @Input() cancelFun: Function;
  receiver_id: any;
  receivers_by_id: any = {};

  constructor(private modalService: NgbModal, private utils: UtilsService, private appDataService: AppDataService) {
  }

  ngOnInit() {
    this.receivers_by_id = this.appDataService.receivers_by_id;
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
