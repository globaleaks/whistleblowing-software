import {Component, Input, OnInit} from "@angular/core";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {FieldUtilitiesService} from "@app/shared/services/field-utilities.service";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {NewStep} from "@app/models/admin/new-step";
import {QuestionnaireService} from "@app/pages/admin/questionnaires/questionnaire.service";

@Component({
  selector: "src-steps",
  templateUrl: "./steps.component.html"
})
export class StepsComponent implements OnInit {
  @Input() questionnaire: any;
  showAddStep: boolean = false;
  step: any;
  editing: boolean = false;
  showAddTrigger: boolean = false;
  new_step: { label: string } = {label: ""};
  parsedFields: any;
  new_trigger: { field: string; option: string; sufficient: boolean } = {
    field: "",
    option: "",
    sufficient: true,
  };

  constructor(private questionnaireService: QuestionnaireService, private fieldUtilities: FieldUtilitiesService, protected node: NodeResolver, protected utilsService: UtilsService, private httpService: HttpService) {
  }

  ngOnInit(): void {
    this.step = this.questionnaire.steps[0];
    this.parsedFields = this.fieldUtilities.parseQuestionnaire(this.questionnaire, {});
  }

  toggleAddStep() {
    this.showAddStep = !this.showAddStep;
  }

  addStep() {
    const step = new NewStep();
    step.questionnaire_id = this.questionnaire.id;
    step.label = this.new_step.label;
    step.order = this.utilsService.newItemOrder(this.questionnaire.steps, "order");

    this.httpService.requestAddAdminQuestionnaireStep(step).subscribe((_: any) => {
      this.new_step = {label: ""};
      return this.questionnaireService.sendData();

    });
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