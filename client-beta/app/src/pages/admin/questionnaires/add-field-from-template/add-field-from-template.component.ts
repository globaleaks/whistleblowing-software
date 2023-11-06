import {Component, EventEmitter, Input, Output} from "@angular/core";
import {HttpService} from "@app/shared/services/http.service";
import {UtilsService} from "@app/shared/services/utils.service";
import {NewField} from "@app/models/admin/new-field";
import {QuestionnaireService} from "@app/pages/admin/questionnaires/questionnaire.service";

@Component({
  selector: "src-add-field-from-template",
  templateUrl: "./add-field-from-template.component.html"
})
export class AddFieldFromTemplateComponent {
  @Input() fieldTemplatesData: any;
  @Input() step: any;
  @Input() type: any;
  @Output() dataToParent = new EventEmitter<string>();

  fields: any = [];
  new_field: any = {};

  constructor(private questionnaireService: QuestionnaireService, private httpService: HttpService, private utilsService: UtilsService) {
    this.new_field = {
      template_id: ""
    };
  }

  ngOnInit(): void {
    if (this.step) {
      this.fields = this.step.children;
    }
  }

  addFieldFromTemplate(): void {
    if (this.type === "step") {
      const field = new NewField();
      field.step_id = this.step.id;
      field.template_id = "";

      field.template_id = this.new_field.template_id;
      field.instance = "reference";
      field.y = this.utilsService.newItemOrder(this.fields, "y");
      this.httpService.requestAddAdminQuestionnaireField(field).subscribe((newField: any) => {
        this.fields.push(newField);
        this.new_field = {
          template_id: ""
        };
        this.dataToParent.emit();
        return this.questionnaireService.sendData();
      });
    }
    if (this.type === "field") {
      const field = new NewField();
      field.step_id = this.step.id;
      field.template_id = "";

      field.template_id = this.new_field.template_id;
      field.instance = "reference";
      field.y = this.utilsService.newItemOrder(this.step.children, "y");
      this.httpService.requestAddAdminQuestionnaireField(field).subscribe((newField: any) => {
        this.step.children.push(newField);
        this.new_field = {
          template_id: ""
        };
        this.dataToParent.emit();
        return this.questionnaireService.sendData();
      });
    }
  }
}