import { Component, Input } from '@angular/core';
import { UtilsService } from '@app/shared/services/utils.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'src-otkc-access',
  templateUrl: './otkc-access.component.html',
})
export class OtkcAccessComponent {
  @Input() arg: { receipt: any, formatted_receipt: any };
 
  confirmFunction: () => void;
  constructor(private modalService: NgbModal, protected utils: UtilsService) {
  }

  confirm() {
    this.confirmFunction();
    this.cancel();
  }

  cancel() {
    this.modalService.dismissAll();
  }
}
