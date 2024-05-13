import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {FieldUtilitiesService} from "@app/shared/services/field-utilities.service";
import {ControlContainer, NgForm} from "@angular/forms";
import {SubmissionService} from "@app/services/helper/submission.service";
import {Answers} from "@app/models/reciever/reciever-tip-data";
import {Children, Step} from "@app/models/whistleblower/wb-tip-data";

@Component({
  selector: "src-form",
  templateUrl: "./form.component.html",
  viewProviders: [{provide: ControlContainer, useExisting: NgForm}],
})
export class FormComponent implements OnInit {
  @Input() step: Step;
  @Input() index: number;
  @Input() answers: Answers;
  @Input() uploads: { [key: string]: any };
  @Input() submission: SubmissionService;
  @Input() displayErrors: boolean;
  @Input() entry: string;
  @Input() identity_provided: any;
  @Input() fileUploadUrl: string;
  @Output() notifyFileUpload: EventEmitter<any> = new EventEmitter<any>();
  @Input() fieldEntry: string;

  fields: Children[];
  stepId: string;
  rows: any;
  status: { opened: boolean };

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
