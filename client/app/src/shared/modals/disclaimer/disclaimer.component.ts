import {Component, OnInit} from "@angular/core";
import {NgbActiveModal, NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {AppDataService} from "@app/app-data.service";
import {Node} from "@app/models/app/public-model";

@Component({
  selector: "src-disclaimer",
  templateUrl: "./disclaimer.component.html",
})
export class DisclaimerComponent implements OnInit {
  nodeData: Node;

  constructor(private activeModal: NgbActiveModal, private modalService: NgbModal, protected appDataService: AppDataService) {
  }

  confirmFunction: () => void;

  ngOnInit(): void {
    if (this.appDataService.public.node) {
      this.nodeData = this.appDataService.public.node;
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
