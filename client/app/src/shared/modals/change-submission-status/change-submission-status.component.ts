import {Component, Input} from "@angular/core";
import {SubmissionStatus} from "@app/models/app/shared-public-model";
import {RecieverTipData} from "@app/models/reciever/reciever-tip-data";
import {NgbActiveModal, NgbModal} from "@ng-bootstrap/ng-bootstrap";
@Component({
  selector: 'src-change-submission-status',
  templateUrl: './change-submission-status.component.html',
})
export class ChangeSubmissionStatusComponent {
  @Input() arg: {tip:RecieverTipData, motivation:string,submission_statuses:SubmissionStatus[],status:any};

  constructor(private modalService: NgbModal, private activeModal: NgbActiveModal) {
  }
  
  confirmFunction: (status:SubmissionStatus,motivation: string) => void;
  
    confirm(status: SubmissionStatus,motivation:string) {
      if(status){
        this.confirmFunction(status,motivation);
        return this.activeModal.close(status);
      }else{
        this.cancel()
      }
    }
  
    cancel() {
      this.modalService.dismissAll();
    }
}
