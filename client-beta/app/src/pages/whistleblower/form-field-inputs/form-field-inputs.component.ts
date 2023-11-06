import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {ControlContainer, NgForm} from "@angular/forms";

@Component({
  selector: "src-form-field-inputs",
  templateUrl: "./form-field-inputs.component.html",
  viewProviders: [{provide: ControlContainer, useExisting: NgForm}],
})
export class FormFieldInputsComponent implements OnInit {
  @Input() field: any;
  @Input() fieldRow: any;
  @Input() fieldCol: any;
  @Input() stepId: any;
  @Input() step: any;
  @Input() entry: any;
  @Input() answers: any;
  @Input() submission: any;
  @Input() index: any;
  @Input() displayErrors: boolean;
  @Input() fields: any;
  @Input() uploads: any;
  @Input() identity_provided: any;
  @Input() fileUploadUrl: any;
  @Output() notifyFileUpload: EventEmitter<any> = new EventEmitter<any>();

  fieldId: string;
  entries: any;
  fieldEntry = "";

  constructor(protected utilsService: UtilsService) {
  }

  ngOnInit(): void {
    this.fieldId = this.stepId + "-field-" + this.fieldRow + "-" + this.fieldCol;
    this.entries = this.getAnswersEntries(this.entry);
    this.fieldEntry = this.fieldId + "-input-" + this.index;
  }

  getAnswersEntries(entry: any) {
    if (!entry || typeof entry === "undefined") {
      return this.answers[this.field.id];
    }

    return entry[this.field.id];
  };

  addAnswerEntry() {
    this.entries.push({});
  };
}
