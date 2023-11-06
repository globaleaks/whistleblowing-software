import {Component, EventEmitter, Input, Output} from "@angular/core";
import {NgForm} from "@angular/forms";
import {UtilsService} from "@app/shared/services/utils.service";
import {SubmissionService} from "@app/services/submission.service";

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
  @Input() context: any;
  @Input() navigation: number;
  @Input() uploads: number;
  @Input() submission: SubmissionService;
  @Input() stepForms: any;
  @Input() field_id_map: any;

  @Input() displayStepErrors: Function;
  @Input() stepForm: Function;

  @Output() goToStep: EventEmitter<any> = new EventEmitter();

  constructor(protected utilsService: UtilsService) {
  }

}
