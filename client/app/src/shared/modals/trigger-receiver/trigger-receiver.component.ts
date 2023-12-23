import {Component, Input} from "@angular/core";
import {NgbActiveModal, NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {UsersResolver} from "@app/shared/resolvers/users.resolver";
import {UtilsService} from "@app/shared/services/utils.service";
import {Option} from "@app/models/app/shared-public-model";
import {userResolverModel} from "@app/models/resolvers/user-resolver-model";

@Component({
  selector: "src-trigger-receiver",
  templateUrl: "./trigger-receiver.component.html"
})
export class TriggerReceiverComponent {

  @Input() arg: Option;
  confirmFunction: (data: Option) => void;

  selected: { value: []; name: string };
  admin_receivers_by_id: { [userId: string]: userResolverModel } = {};
  userData: userResolverModel[] = [];

  constructor(private utilsService: UtilsService, private users: UsersResolver, private activeModal: NgbActiveModal, private modalService: NgbModal) {
  }

  ngOnInit(): void {
    this.selected = {value: [], name: ""};
    if (Array.isArray(this.users.dataModel)) {
      this.userData = this.users.dataModel;
    } else {
      this.userData = [this.users.dataModel];
    }
    this.admin_receivers_by_id = this.utilsService.array_to_map(this.users.dataModel);
  }

  confirm() {
    this.confirmFunction(this.arg);
    return this.activeModal.close(this.arg);
  }

  cancel() {
    this.modalService.dismissAll();
  }

  addReceiver(item: userResolverModel) {
    if (item && this.arg.trigger_receiver.indexOf(item.id) === -1) {
      this.arg.trigger_receiver.push(item.id);
    }
  }


  removeReceiver(index: number) {
    this.arg.trigger_receiver.splice(index, 1);
  }

  resetRecipients() {
    this.arg.trigger_receiver = [];
    this.modalService.dismissAll();
  }

}