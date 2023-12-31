import {Component, OnInit} from "@angular/core";
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";
import {UtilsService} from "@app/shared/services/utils.service";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import {Constants} from "@app/shared/constants/constants";

@Component({
  selector: "src-request-support",
  templateUrl: "./request-support.component.html"
})
export class RequestSupportComponent implements OnInit {
  protected readonly Constants = Constants;
  sent = false;
  arg: { mail_address: string, text: string } = {mail_address: "", text: ""};

  constructor(protected activeModal: NgbActiveModal, protected utilsService: UtilsService, private preferenceResolver: PreferenceResolver) {
  }

  ngOnInit(): void {
    this.arg.mail_address = this.preferenceResolver.dataModel.mail_address;
  }
}