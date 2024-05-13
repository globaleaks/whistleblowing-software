import {Component, Input} from "@angular/core";
import {NgbActiveModal, NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {Option} from "@app/models/app/shared-public-model";

@Component({
  selector: "src-add-option-hint",
  templateUrl: "./add-option-hint.component.html"
})
export class AddOptionHintComponent {
  confirmFunction: (data: Option) => void;
  @Input() arg: Option;

  constructor(private activeModal: NgbActiveModal, private modalService: NgbModal) {
  }

  confirm() {
    this.confirmFunction(this.arg);
    return this.activeModal.close(this.arg);
  }

  cancel() {
    this.modalService.dismissAll();
  }

}
