import {Component, EventEmitter, Input, OnInit, Output} from "@angular/core";
import {ControlContainer, NgForm} from "@angular/forms";

@Component({
  selector: "src-whistleblower-identity-field",
  templateUrl: "./whistleblower-identity-field.component.html",
  viewProviders: [{provide: ControlContainer, useExisting: NgForm}]
})
export class WhistleblowerIdentityFieldComponent implements OnInit {
  @Input() submission: any;
  @Input() field: any;
  @Output() stateChanged = new EventEmitter<boolean>();

  @Input() stepId: any;
  @Input() fieldCol: any;
  @Input() fieldRow: any;
  @Input() index: any;
  @Input() step: any;
  @Input() answers: any;
  @Input() entry: any;
  @Input() fields: any;
  @Input() displayErrors: any;
  @Input() identity_provided: any = false;
  @Input() identityChanged: any;

  ngOnInit(): void {
    this.identity_provided = true;
    this.stateChanged.emit(true);
    if (this.submission) {
      this.submission._submission.identity_provided = true;
    }
  }

  changeIdentitySetting(status: boolean): void {
    this.identity_provided = status;
    if (this.submission) {
      this.submission._submission.identity_provided = status;
    }
    this.stateChanged.emit(status);
  }
}
