import { Component, EventEmitter, Input, OnInit, Output } from "@angular/core";
import { FieldUtilitiesService } from "@app/shared/services/field-utilities.service";
import { ControlContainer, NgForm } from "@angular/forms";
import { SubmissionService } from "@app/services/submission.service";
import { NgbDateStruct } from "@ng-bootstrap/ng-bootstrap";

@Component({
  selector: "src-form-field-input",
  templateUrl: "./form-field-input.component.html",
  viewProviders: [{provide: ControlContainer, useExisting: NgForm}]
})
export class FormFieldInputComponent implements OnInit {

  @Input() field: any;
  @Input() index: any;
  @Input() step: any;
  @Input() submission: SubmissionService;
  @Input() entryIndex: any;
  @Input() fieldEntry: any;
  @Input() entry: any;
  @Input() fieldId: any;
  @Input() displayErrors: boolean;
  @Input() answers: any;
  @Input() fields: any;
  @Input() uploads: any;
  @Input() identity_provided: any;
  @Input() fileUploadUrl: any;
  @Output() notifyFileUpload: EventEmitter<any> = new EventEmitter<any>();

  entryValue: any = "";
  fieldFormVar: any = {};
  fieldFormVarName: any;
  input_entryIndex = "";
  input_date: NgbDateStruct;
  input_start_date: any;
  input_end_date: any;
  validator: any;
  rows: any;
  dateRange: any = {
    "start": "",
    "end": ""
  };
  dateOptions1: any = {};
  dateOptions2: any = {};
  dateOptions: any = {};

  constructor(private fieldUtilitiesService: FieldUtilitiesService) {
  }

  clearDateRange() {
    this.input_start_date = "";
    this.input_end_date = "";
    this.dateRange = {
      "start": "",
      "end": ""
    };
    this.entry.value = "";
  }

  initializeFormNames() {
    this.input_entryIndex = "input-" + this.entryIndex;
  }

  ngOnInit(): void {
    this.entry["value"] = "";
    this.fieldFormVarName = this.fieldUtilitiesService.fieldFormName(this.field.id + "$" + this.index);
    this.initializeFormNames();
    this.fieldEntry = this.fieldId + "-input-" + this.index;
    this.rows = this.fieldUtilitiesService.splitRows(this.field.children);
    if (this.field.type === "inputbox") {
      const validator_regex = this.fieldUtilitiesService.getValidator(this.field);
      if (validator_regex.length > 0) {
        this.validator = validator_regex;
      }
    }
    if (this.field.type === "date") {
      if (this.field.attrs.min_date) {
        this.dateOptions.min_date = this.field.attrs.min_date.value;
      }
      if (this.field.attrs.max_date) {
        this.dateOptions.max_date = this.field.attrs.max_date.value;
      }
    }
    if (this.field.type === "daterange") {
      if (this.field.attrs.min_date) {
        this.dateOptions1 = this.field.attrs.min_date.value;
      }
      if (this.field.attrs.max_date) {
        this.dateOptions2 = this.field.attrs.max_date.value;
      }
    }
  }

  onDateSelection() {
    this.entry.value = this.convertNgbDateToISOString(this.input_date);
  }

  convertNgbDateToISOString(date: NgbDateStruct): string {
    const jsDate = new Date(date.year, date.month - 1, date.day);
    return jsDate.toISOString();
  }

  onStartDateSelection(date: NgbDateStruct): void {
    const startDate = new Date(date.year, date.month - 1, date.day);
    this.dateRange.start = startDate.getTime().toString();
    this.entry.value = `${this.dateRange.start}:${this.dateRange.end}`;
  }

  onEndDateSelection(date: NgbDateStruct): void {
    const endDate = new Date(date.year, date.month - 1, date.day);
    this.dateRange.end = endDate.getTime().toString();
    this.entry.value = `${this.dateRange.start}:${this.dateRange.end}`;
  }

  validateUploadSubmission() {
    return !!(this.uploads && this.uploads[this.field ? this.field.id : "status_page"] !== undefined && (this.field.type === "fileupload" && this.uploads && this.uploads[this.field ? this.field.id : "status_page"] && Object.keys(this.uploads[this.field ? this.field.id : "status_page"]).length === 0));
  }
}
