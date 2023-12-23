import {ChangeDetectorRef, Component, Input, OnInit} from "@angular/core";
import {Questionnaire} from "@app/models/app/public-model";
import {ParsedFields} from "@app/models/component-model/parsedFields";
import {fieldtemplatesResolverModel} from "@app/models/resolvers/field-template-model";
import {Step} from "@app/models/resolvers/questionnaire-model";
import {FieldTemplatesResolver} from "@app/shared/resolvers/field-templates-resolver.service";
import {HttpService} from "@app/shared/services/http.service";

@Component({
  selector: "src-step",
  templateUrl: "./step.component.html"
})
export class StepComponent implements OnInit {
  @Input() step: Step;
  @Input() parsedFields: ParsedFields;
  showAddQuestion: boolean = false;
  showAddQuestionFromTemplate: boolean = false;
  fieldTemplatesData: fieldtemplatesResolverModel[] = [];

  constructor(private cdr: ChangeDetectorRef, private httpService: HttpService, protected fieldTemplates: FieldTemplatesResolver) {
  }

  ngOnInit(): void {
    if (Array.isArray(this.fieldTemplates.dataModel)) {
      this.fieldTemplatesData = this.fieldTemplates.dataModel;
    } else {
      this.fieldTemplatesData = [this.fieldTemplates.dataModel];
    }
  }

  toggleAddQuestion(): void {
    this.showAddQuestion = !this.showAddQuestion;
    this.showAddQuestionFromTemplate = false;
  }

  toggleAddQuestionFromTemplate(): void {
    this.showAddQuestionFromTemplate = !this.showAddQuestionFromTemplate;
    this.showAddQuestion = false;
  }

  listenToAddField() {
    this.showAddQuestion = false;
  }

  listenToAddFieldFormTemplate() {
    this.showAddQuestionFromTemplate = false;
  }
  listenToFields() {
    this.getResolver()
  }
  
  getResolver() {
    return this.httpService.requestQuestionnairesResource().subscribe(response => {
      response.forEach((step: Questionnaire) => {
        if (step.id == this.step.questionnaire_id) {
          step.steps.forEach((innerStep: any) => {
            if (innerStep.id == this.step.id) {
              this.step = innerStep;
            }
          })
          this.cdr.markForCheck();
        }
      });
    });
  }
}