import {Component, OnInit} from "@angular/core";
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";
import { AppDataService } from "@app/app-data.service";
import { preferenceResolverModel } from "@app/models/resolvers/preference-resolver-model";

@Component({
  selector: "src-accept-agreement",
  templateUrl: "./accept-agreement.component.html",
})
export class AcceptAgreementComponent implements OnInit {
  confirmFunction: () => void;
  preferenceData: preferenceResolverModel;
  accept: boolean = false;

  constructor(private activeModal: NgbActiveModal, private preference: PreferenceResolver,public appDataService: AppDataService) {
  }

  ngOnInit(): void {
    if (this.preference.dataModel) {
      this.preferenceData = this.preference.dataModel;
    }
  }

  confirm() {
    this.confirmFunction();
    return this.activeModal.close();
  }
}
