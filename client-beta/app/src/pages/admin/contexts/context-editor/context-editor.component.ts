import {HttpClient} from "@angular/common/http";
import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {NgForm} from "@angular/forms";
import {AcceptAgreementComponent} from "@app/shared/modals/accept-agreement/accept-agreement.component";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {DeleteConfirmationComponent} from "@app/shared/modals/delete-confirmation/delete-confirmation.component";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {QuestionnairesResolver} from "@app/shared/resolvers/questionnaires.resolver";
import {UsersResolver} from "@app/shared/resolvers/users.resolver";
import {UtilsService} from "@app/shared/services/utils.service";
import {Observable} from "rxjs";

@Component({
  selector: "src-context-editor",
  templateUrl: "./context-editor.component.html"
})
export class ContextEditorComponent implements OnInit {
  @Input() contextsData: any[];
  @Input() context: any;
  @Input() index: any;
  @Input() editContext: NgForm;
  @Output() dataToParent = new EventEmitter<string>();
  editing: boolean = false;
  showAdvancedSettings: boolean = false;
  showSelect: boolean = false;
  questionnairesData: any = [];
  usersData: any = [];
  nodeData: any = [];
  selected = {value: null};
  adminReceiversById: any;

  constructor(private http: HttpClient, private modalService: NgbModal, protected nodeResolver: NodeResolver, private usersResolver: UsersResolver, private questionnairesResolver: QuestionnairesResolver, private utilsService: UtilsService) {
  }

  ngOnInit(): void {
    this.questionnairesData = this.questionnairesResolver.dataModel;
    this.usersData = this.usersResolver.dataModel;
    this.nodeData = this.nodeResolver.dataModel;
    this.adminReceiversById = this.utilsService.array_to_map(this.usersResolver.dataModel);
  }

  toggleEditing(): void {
    this.editing = !this.editing;
  }

  swap($event: any, index: number, n: number): void {
    $event.stopPropagation();

    const target = index + n;
    if (target < 0 || target >= this.contextsData.length) {
      return;
    }

    [this.contextsData[index], this.contextsData[target]] =
      [this.contextsData[target], this.contextsData[index]];

    this.http.put("api/admin/contexts", {
      operation: "order_elements",
      args: {ids: this.contextsData.map(c => c.id)},
    }).subscribe();
  }

  moveUp(e: any, idx: number): void {
    this.swap(e, idx, -1);
  }

  moveDown(e: any, idx: number): void {
    this.swap(e, idx, 1);
  }

  swapReceiver(index: number, n: number): void {
    const target = index + n;
    if (target > -1 && target < this.context.receivers.length) {
      const tmp = this.context.receivers[target];
      this.context.receivers[target] = this.context.receivers[index];
      this.context.receivers[index] = tmp;
    }
  }

  receiverNotSelectedFilter(item: any): boolean {
    return this.context.receivers.indexOf(item.id) === -1;
  }

  moveUpReceiver(index: number): void {
    this.swapReceiver(index, -1);
  }

  moveDownReceiver(index: number): void {
    this.swapReceiver(index, 1);
  }

  toggleSelect(): void {
    this.showSelect = true;
  }

  moveReceiver(rec: any): void {
    if (rec && this.context.receivers.indexOf(rec.id) === -1) {
      this.context.receivers.push(rec.id);
      this.showSelect = false;
    }
  }

  deleteContext(context: any): void {
    this.openConfirmableModalDialog(context, "").subscribe();
  }

  openConfirmableModalDialog(arg: any, scope: any): Observable<string> {
    scope = !scope ? this : scope;
    return new Observable((observer) => {
      let modalRef = this.modalService.open(DeleteConfirmationComponent, {});
      modalRef.componentInstance.arg = arg;
      modalRef.componentInstance.scope = scope;
      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
        return this.utilsService.deleteAdminContext(arg.id).subscribe(_ => {
          this.utilsService.deleteResource(this.contextsData,arg);
        });
      };
    });
  }

  saveContext(context: any) {
    if (context.additional_questionnaire_id === null) {
      context.additional_questionnaire_id = "";
    }
    this.utilsService.updateAdminContext(context, context.id).subscribe(_ => {
      this.sendDataToParent();
    });
  }

  sendDataToParent() {
    this.dataToParent.emit();
  }
}