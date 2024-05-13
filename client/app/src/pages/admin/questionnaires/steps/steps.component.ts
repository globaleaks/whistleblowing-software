import {Component, Input, OnInit} from "@angular/core";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {NewStep} from "@app/models/admin/new-step";
import {QuestionnaireService} from "@app/pages/admin/questionnaires/questionnaire.service";
import {Step, questionnaireResolverModel} from "@app/models/resolvers/questionnaire-model";

@Component({
  selector: "src-steps",
  templateUrl: "./steps.component.html"
})
export class StepsComponent implements OnInit {
  @Input() questionnaire: questionnaireResolverModel;
  showAddStep: boolean = false;
  step: Step;
  editing: boolean = false;
  new_step: { label: string } = {label: ""};

  constructor(private questionnaireService: QuestionnaireService, protected node: NodeResolver, protected utilsService: UtilsService, private httpService: HttpService) {
  }

  ngOnInit(): void {
    this.step = this.questionnaire.steps[0];
  }

  toggleAddStep() {
    this.showAddStep = !this.showAddStep;
  }

  addStep() {
    const step = new NewStep();
    step.questionnaire_id = this.questionnaire.id;
    step.label = this.new_step.label;
    step.order = this.utilsService.newItemOrder(this.questionnaire.steps, "order");

    this.httpService.requestAddAdminQuestionnaireStep(step).subscribe(() => {
      this.new_step = {label: ""};
      return this.questionnaireService.sendData();

    });
  }
}