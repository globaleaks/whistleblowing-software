import {Component} from "@angular/core";
import {NgbActiveModal, NgbModal} from "@ng-bootstrap/ng-bootstrap";

@Component({
  selector: 'src-reopen-submission',
  templateUrl: './reopen-submission.component.html',
})
export class ReopenSubmissionComponent {
  arg:{ motivation: string}={motivation: ""};
  constructor(private modalService: NgbModal, private activeModal: NgbActiveModal) {
  }
 
  confirmFunction: (motivation: string) => void;
  
    confirm(arg: string) {
      this.confirmFunction(arg);
      return this.activeModal.close(arg);
    }
  
    cancel() {
      this.modalService.dismissAll();
    }
}
