import {Component, EventEmitter, Input, Output} from "@angular/core";
import {NgForm} from "@angular/forms";
import {AssignScorePointsComponent} from "@app/shared/modals/assign-score-points/assign-score-points.component";
import {DeleteConfirmationComponent} from "@app/shared/modals/delete-confirmation/delete-confirmation.component";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {QuestionnaireDuplicationComponent} from "@app/shared/modals/questionnaire-duplication/questionnaire-duplication.component";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {QuestionnaireService} from "@app/pages/admin/questionnaires/questionnaire.service";
import {Observable} from "rxjs";

@Component({
  selector: "src-questionnaires-list",
  templateUrl: "./questionnaires-list.component.html"
})
export class QuestionnairesListComponent {
  @Input() questionnaire: any;
  @Input() questionnaires: any;
  @Input() editQuestionnaire: NgForm;
  showAddQuestion: boolean = false;
  editing: boolean = false;
  @Output() deleteRequestData = new EventEmitter<string>();

  constructor(private questionnaireService: QuestionnaireService, private modalService: NgbModal, private httpService: HttpService, private utilsService: UtilsService) {
  }

  toggleAddQuestion(): void {
    this.showAddQuestion = !this.showAddQuestion;
  }

  toggleEditing(questionnaire: any) {
    this.editing = questionnaire.editable && !this.editing;
  }

  saveQuestionnaire(questionnaire: any) {
    this.httpService.requestUpdateAdminQuestionnaire(questionnaire.id, questionnaire).subscribe(_ => {
      this.editing = false;
      return this.questionnaireService.sendData();
    });
  }

  exportQuestionnaire(questionnaire: any) {
    this.utilsService.saveAs(questionnaire.name, "api/admin/questionnaires/" + questionnaire.id,);
  }

  duplicateQuestionnaire(questionnaire: any) {
    const modalRef = this.modalService.open(QuestionnaireDuplicationComponent);
    modalRef.componentInstance.questionnaire = questionnaire;
    modalRef.componentInstance.operation = "duplicate";
    return modalRef.result;
  }

  deleteQuestionnaire(questionnaire: any) {
    this.openConfirmableModalDialog(questionnaire, "").subscribe();
  }

  openConfirmableModalDialog(arg: any, scope: any): Observable<string> {
    scope = !scope ? this : scope;
    return new Observable((observer) => {
      let modalRef = this.modalService.open(DeleteConfirmationComponent, {});
      modalRef.componentInstance.arg = arg;
      modalRef.componentInstance.scope = scope;

      modalRef.componentInstance.confirmFunction = () => {
        observer.complete()
        return this.httpService.requestDeleteAdminQuestionnaire(arg.id).subscribe(_ => {
          this.utilsService.deleteResource(this.questionnaires,arg);
        });
      };
    });
  }
}