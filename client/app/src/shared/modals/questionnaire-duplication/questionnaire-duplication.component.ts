import {HttpClient} from "@angular/common/http";
import {Component, Input} from "@angular/core";
import {NgbModal} from "@ng-bootstrap/ng-bootstrap";
import {UtilsService} from "@app/shared/services/utils.service";
import {questionnaireResolverModel} from "@app/models/resolvers/questionnaire-model";

@Component({
  selector: "src-questionnaire-duplication",
  templateUrl: "./questionnaire-duplication.component.html"
})
export class QuestionnaireDuplicationComponent {
  @Input() questionnaire: questionnaireResolverModel;
  @Input() operation: string;
  duplicate_questionnaire: { name: string } = {name: ""};

  constructor(private utilsService: UtilsService, private http: HttpClient, private modalService: NgbModal) {
  }

  cancel() {
    this.modalService.dismissAll();
  }

  confirm() {
    if (this.operation === "duplicate" && this.duplicate_questionnaire.name.length > 0) {
      this.http.post(
        "api/admin/questionnaires/duplicate",
        {
          questionnaire_id: this.questionnaire.id,
          new_name: this.duplicate_questionnaire.name
        }
      ).subscribe(() => {
        this.modalService.dismissAll();
        this.utilsService.reloadComponent();
      });
    } else {
      this.modalService.dismissAll();
    }
  }
}
