import {Component, Input} from "@angular/core";
import {NgbActiveModal, NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {UsersResolver} from "@app/shared/resolvers/users.resolver";
import {UtilsService} from "@app/shared/services/utils.service";

@Component({
  selector: "src-trigger-receiver",
  templateUrl: "./trigger-receiver.component.html"
})
export class TriggerReceiverComponent {

  @Input() arg: any;
  confirmFunction: (data: any) => void;

  selected: { value: any; name: string };
  admin_receivers_by_id: any = {};
  userData: any = [];

  constructor(private utilsService: UtilsService, private users: UsersResolver, private activeModal: NgbActiveModal, private modalService: NgbModal) {
  }

  ngOnInit(): void {
    this.selected = {value: "", name: ""};
    this.userData = this.users.dataModel;
    this.admin_receivers_by_id = this.utilsService.array_to_map(this.users.dataModel);
  }

  confirm() {
    this.confirmFunction(this.arg);
    return this.activeModal.close(this.arg);
  }

  cancel() {
    this.modalService.dismissAll();
  }

  addReceiver(item: any) {
    if (item && this.arg.trigger_receiver.indexOf(item.id) === -1) {
      this.arg.trigger_receiver.push(item.id);
    }
  }


  removeReceiver(index: number) {
    this.arg.trigger_receiver.splice(index, 1);
  }

  resetRecipients() {
    this.arg.trigger_receiver = [];
  }

}