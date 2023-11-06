import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {NgForm} from "@angular/forms";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {AddOptionHintComponent} from "@app/shared/modals/add-option-hint/add-option-hint.component";
import {AssignScorePointsComponent} from "@app/shared/modals/assign-score-points/assign-score-points.component";
import {DeleteConfirmationComponent} from "@app/shared/modals/delete-confirmation/delete-confirmation.component";
import {TriggerReceiverComponent} from "@app/shared/modals/trigger-receiver/trigger-receiver.component";
import {FieldTemplatesResolver} from "@app/shared/resolvers/field-templates-resolver.service";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {FieldUtilitiesService} from "@app/shared/services/field-utilities.service";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {QuestionnaireService} from "@app/pages/admin/questionnaires/questionnaire.service";
import {Observable} from "rxjs";

@Component({
  selector: "src-fields",
  templateUrl: "./fields.component.html"
})
export class FieldsComponent implements OnInit {
  @Input() editField: NgForm;
  @Input() field: any;
  @Input() fields: any;
  @Input() type: any;
  @Output() dataToParent = new EventEmitter<string>();

  editing: boolean = false;
  openMinDate: boolean = false;
  openMaxDate: boolean = false;
  showAddTrigger: boolean = false;
  showAddQuestionFromTemplate: boolean = false;
  showAddQuestion: boolean = false;
  fieldIsMarkableSubjectToStats: any;
  fieldIsMarkableSubjectToPreview: any;
  fieldTemplatesData: any = [];
  children: any;
  new_trigger: { field: string; option: string; sufficient: boolean } = {
    field: "",
    option: "",
    sufficient: false,
  };
  parsedFields: any;

  constructor(private questionnaireService: QuestionnaireService, private modalService: NgbModal, public nodeResolver: NodeResolver, private httpService: HttpService, private utilsService: UtilsService, private fieldTemplates: FieldTemplatesResolver, private fieldUtilities: FieldUtilitiesService,) {
  }

  ngOnInit(): void {
    this.fieldTemplatesData = this.fieldTemplates.dataModel;
    this.fieldIsMarkableSubjectToStats = this.isMarkableSubjectToStats(this.field);
    this.fieldIsMarkableSubjectToPreview = this.isMarkableSubjectToPreview(this.field);
    this.parsedFields = this.fieldUtilities.parseFields(this.fieldTemplates.dataModel, {});
    this.children = this.field.children;
  }

  saveField(field: any) {
    this.utilsService.assignUniqueOrderIndex(field.options);
    return this.httpService.requestUpdateAdminQuestionnaireField(field.id, field).subscribe(_ => {
        this.dataToParent.emit()
    });
  }
  toggleEditing() {
    this.editing = !this.editing;
  }

  exportQuestion(field: any) {
    this.utilsService.download("api/admin/fieldtemplates/" + field.id);
  }

  delField(field: any) {
    this.openConfirmableModalDialog(field, "").subscribe();
  }

  openConfirmableModalDialog(arg: any, scope: any): Observable<string> {
    return new Observable((observer) => {
      let modalRef = this.modalService.open(DeleteConfirmationComponent, {});
      modalRef.componentInstance.arg = arg;
      modalRef.componentInstance.scope = scope;

      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
        return this.httpService.requestDeleteAdminQuestionareField(arg.id).subscribe(() => {
          return this.utilsService.deleteResource(this.fields,arg);
        });
      };
    });
  }

  moveUpAndSave(field: any): void {
    this.utilsService.moveUp(field);
    this.saveField(field);
  }

  moveDownAndSave(field: any): void {
    this.utilsService.moveDown(field);
    this.saveField(field);
  }

  moveLeftAndSave(field: any): void {
    this.utilsService.moveLeft(field);
    this.saveField(field);
  }

  moveRightAndSave(field: any): void {
    this.utilsService.moveRight(field);
    this.saveField(field);
  }

  typeSwitch(type: string): string {
    if (["inputbox", "textarea"].indexOf(type) !== -1) {
      return "inputbox_or_textarea";
    }

    if (["checkbox", "selectbox"].indexOf(type) !== -1) {
      return "checkbox_or_selectbox";
    }

    return type;
  }

  isMarkableSubjectToStats(field: any): boolean {
    return ["inputbox", "textarea", "fieldgroup"].indexOf(field.type) === -1;
  }

  isMarkableSubjectToPreview(field: any): boolean {
    return ["fieldgroup", "fileupload"].indexOf(field.type) === -1;
  }

  toggleMinDate() {
    this.openMinDate = !this.openMinDate;
  }

  toggleMaxDate() {
    this.openMaxDate = !this.openMaxDate;
  }

  toggleAddTrigger() {
    this.showAddTrigger = !this.showAddTrigger;
  };

  delTrigger(trigger: any): void {
    const index = this.field.triggered_by_options.indexOf(trigger);
    if (index !== -1) {
      this.field.triggered_by_options.splice(index, 1);
    }
  }

  addTrigger() {
    this.field.triggered_by_options.push(this.new_trigger);
    this.toggleAddTrigger();
    this.new_trigger = {"field": "", "option": "", "sufficient": false};
  }

  showOptions(field: any): boolean {
    if (field.instance === "reference") {
      return false;
    }

    return ["checkbox", "selectbox", "multichoice"].indexOf(field.type) > -1;
  }

  addOption(): void {
    const new_option: any = {
      id: "",
      label: "",
      hint1: "",
      hint2: "",
      block_submission: false,
      score_points: 0,
      score_type: "none",
      trigger_receiver: [],
    };

    new_option.order = this.utilsService.newItemOrder(this.field.options, "order");

    this.field.options.push(new_option);
  }

  delOption(option: any): void {
    const index = this.field.options.indexOf(option);
    if (index !== -1) {
      this.field.options.splice(index, 1);
    }
  }

  moveOptionUp(idx: number): void {
    this.swapOption(idx, -1);
  }

  moveOptionDown(idx: number): void {
    this.swapOption(idx, 1);
  }

  addOptionHintDialog(option: any) {
    this.openOptionHintDialog(option).subscribe();

  }

  openOptionHintDialog(arg: any): Observable<string> {
    return new Observable((observer) => {
      let modalRef = this.modalService.open(AddOptionHintComponent, {});
      modalRef.componentInstance.arg = arg;

      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
      };
    });
  }

  private swapOption(index: number, n: number): void {
    const target = index + n;
    if (target < 0 || target >= this.field.options.length) {
      return;
    }
    const indexA = this.field.options[target];
    this.field.options[target] = this.field.options[index];
    this.field.options[index] = indexA;
  }

  flipBlockSubmission(option: any): void {
    option.block_submission = !option.block_submission;
  }

  triggerReceiverDialog(option: any): void {
    this.openTriggerReceiverDialog(option).subscribe();

  }

  openTriggerReceiverDialog(arg: any): Observable<string> {
    return new Observable((observer) => {
      let modalRef = this.modalService.open(TriggerReceiverComponent, {});
      modalRef.componentInstance.arg = arg;

      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
      };
    });
  }

  assignScorePointsDialog(option: any) {
    this.openAssignScorePointsDialog(option).subscribe();
  }

  openAssignScorePointsDialog(arg: any): Observable<string> {
    return new Observable((observer) => {
      let modalRef = this.modalService.open(AssignScorePointsComponent, {});
      modalRef.componentInstance.arg = arg;

      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
      };
    });
  }

  toggleAddQuestionFromTemplate() {
    this.showAddQuestionFromTemplate = !this.showAddQuestionFromTemplate;
    this.showAddQuestion = false;
  }

  toggleAddQuestion() {
    this.showAddQuestion = !this.showAddQuestion;
    this.showAddQuestionFromTemplate = false;
  }

  listenToAddField() {
    this.showAddQuestion = false;
  }

  listenToAddFieldFormTemplate() {
    this.showAddQuestionFromTemplate = false;
  }
}