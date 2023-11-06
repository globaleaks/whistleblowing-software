import {Component, Input} from "@angular/core";
import {AssignScorePointsComponent} from "@app/shared/modals/assign-score-points/assign-score-points.component";
import {DeleteConfirmationComponent} from "@app/shared/modals/delete-confirmation/delete-confirmation.component";
import {UtilsService} from "@app/shared/services/utils.service";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {FieldUtilitiesService} from "@app/shared/services/field-utilities.service";
import {HttpService} from "@app/shared/services/http.service";
import {QuestionnaireService} from "@app/pages/admin/questionnaires/questionnaire.service";
import {Observable} from "rxjs";

@Component({
  selector: "src-steps-list",
  templateUrl: "./steps-list.component.html"
})
export class StepsListComponent {
  @Input() step: any;
  @Input() steps: any;
  @Input() questionnaire: any;
  @Input() index: any;
  editing: boolean = false;
  showAddTrigger: boolean = false;
  parsedFields: any;
  new_trigger: { field: string; option: string; sufficient: boolean } = {
    field: "",
    option: "",
    sufficient: true,
  };

  constructor(private utilsService: UtilsService, private questionnaireService: QuestionnaireService, private modalService: NgbModal, private fieldUtilities: FieldUtilitiesService, protected nodeResolver: NodeResolver, private httpService: HttpService) {
  }

  ngOnInit(): void {
    this.parsedFields = this.fieldUtilities.parseQuestionnaire(this.questionnaire, {});
  }

  swap($event: any, index: number, n: number): void {
    this.utilsService.swap($event, index,n , this.questionnaire)
  }

  moveUp(e: any, idx: number): void {
    this.swap(e, idx, -1);
  }

  moveDown(e: any, idx: number): void {
    this.swap(e, idx, 1);
  }

  toggleEditing() {
    this.editing = !this.editing;
  }

  toggleAddTrigger() {
    this.showAddTrigger = !this.showAddTrigger;
  }

  saveStep(step: any) {
    return this.httpService.requestUpdateAdminQuestionnaireStep(step.id, step).subscribe(_ => {
      return this.questionnaireService.sendData();
    });
  }

  deleteStep(step: any) {
    this.openConfirmableModalDialog(step, "").subscribe();
  }

  openConfirmableModalDialog(arg: any, scope: any): Observable<string> {
    scope = !scope ? this : scope;
    return new Observable((observer) => {
      let modalRef = this.modalService.open(DeleteConfirmationComponent, {});
      modalRef.componentInstance.arg = arg;
      modalRef.componentInstance.scope = scope;

      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
        return this.httpService.requestDeleteAdminQuestionareStep(arg.id).subscribe(_ => {
          this.utilsService.deleteResource(this.steps,arg);
        });
      };
    });
  }

  addTrigger() {
    this.step.triggered_by_options.push(this.new_trigger);
    this.toggleAddTrigger();
    this.new_trigger = {"field": "", "option": "", "sufficient": true};
  }

  delTrigger(trigger: any) {
    const index = this.step.triggered_by_options.indexOf(trigger);
    if (index !== -1) {
      this.step.triggered_by_options.splice(index, 1);
    }
  }
}