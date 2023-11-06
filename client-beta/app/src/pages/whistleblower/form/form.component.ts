import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {FieldUtilitiesService} from "@app/shared/services/field-utilities.service";
import {ControlContainer, NgForm} from "@angular/forms";

@Component({
  selector: "src-form",
  templateUrl: "./form.component.html",
  viewProviders: [{provide: ControlContainer, useExisting: NgForm}],
})
export class FormComponent implements OnInit {
  @Input() step: any;
  @Input() index: any;
  @Input() answers: any;
  @Input() uploads: any;
  @Input() submission: any;
  @Input() displayErrors: boolean;
  @Input() entry: any;
  @Input() identity_provided: any;
  @Input() fileUploadUrl: any;
  @Output() notifyFileUpload: EventEmitter<any> = new EventEmitter<any>();

  fields: any;
  stepId: string;
  rows: any;
  status: any = {};

  constructor(protected fieldUtilitiesService: FieldUtilitiesService) {
  }

  ngOnInit(): void {
    this.initialize();
  }

  initialize() {
    if (this.step.children) {
      this.fields = this.step.children;
    } else {
      this.fields = [];
    }
    this.stepId = "step-" + this.index;
    this.rows = this.fieldUtilitiesService.splitRows(this.fields);
    if (this.rows.length === 0) {
      this.rows = this.step;
    }
    this.status = {
      opened: false,
    };
  }
}
