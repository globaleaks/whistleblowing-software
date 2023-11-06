import {Component, OnInit} from "@angular/core";
import {NgbActiveModal} from "@ng-bootstrap/ng-bootstrap";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {PreferenceResolver} from "@app/shared/resolvers/preference.resolver";

@Component({
  selector: "src-accept-agreement",
  templateUrl: "./accept-agreement.component.html",
})
export class AcceptAgreementComponent implements OnInit {
  confirmFunction: () => void;
  nodeData: any = [];
  preferenceData: any = [];
  accept: boolean = false;

  constructor(private activeModal: NgbActiveModal, private preference: PreferenceResolver, private nodeResolver: NodeResolver) {
  }

  ngOnInit(): void {
    if (this.nodeResolver.dataModel) {
      this.nodeData = this.nodeResolver.dataModel;
    }
    if (this.preference.dataModel) {
      this.preferenceData = this.preference.dataModel;
    }
  }

  confirm() {
    this.confirmFunction();
    return this.activeModal.close();
  }
}
