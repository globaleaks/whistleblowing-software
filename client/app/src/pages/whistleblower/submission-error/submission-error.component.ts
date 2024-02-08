import {Component, EventEmitter, Input, Output, QueryList} from "@angular/core";
import {NgForm} from "@angular/forms";
import {UtilsService} from "@app/shared/services/utils.service";
import {SubmissionService} from "@app/services/helper/submission.service";
import {Field} from "@app/models/resolvers/field-template-model";
import {Context} from "@app/models/reciever/reciever-tip-data";
import {DisplayStepErrorsFunction, StepFormFunction} from "@app/shared/constants/types";

@Component({
  selector: "src-submission-error",
  templateUrl: "./submission-error.component.html"
})
export class SubmissionErrorComponent {

  @Input() submissionForm: NgForm;
  @Input() hasPreviousStep: boolean;
  @Input() show_steps_navigation_interface: boolean;
  @Input() hasNextStep: boolean;
  @Input() areReceiverSelected: boolean;
  @Input() singleStepForm: boolean;
  @Input() context: Context;
  @Input() navigation: number;
  @Input() uploads: { [key: string]: any };
  @Input() submission: SubmissionService;
  @Input() stepForms: QueryList<NgForm>;
  @Input() field_id_map: { [key: string]: Field };

  @Input() displayStepErrors: DisplayStepErrorsFunction ;
  @Input() stepForm: StepFormFunction;

  @Output() goToStep: EventEmitter<any> = new EventEmitter();

  constructor(protected utilsService: UtilsService) {
  }

}
