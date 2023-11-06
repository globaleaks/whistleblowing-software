import {Component, OnInit} from "@angular/core";
import {NgbActiveModal, NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";

@Component({
  selector: "src-disclaimer",
  templateUrl: "./disclaimer.component.html",
})
export class DisclaimerComponent implements OnInit {
  nodeData: any = [];

  constructor(private activeModal: NgbActiveModal, private modalService: NgbModal, protected nodeResolver: NodeResolver) {
  }

  confirmFunction: () => void;

  ngOnInit(): void {
    if (this.nodeResolver.dataModel) {
      this.nodeData = this.nodeResolver.dataModel;
    }
  }

  confirm() {
    this.confirmFunction();
    return this.activeModal.close();
  }

  cancel() {
    this.modalService.dismissAll();
  }
}
