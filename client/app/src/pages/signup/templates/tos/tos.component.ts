import {Component, Input} from "@angular/core";
import {AppDataService} from "@app/app-data.service";
import {ControlContainer, NgForm} from "@angular/forms";
import {Signup} from "@app/models/component-model/signup";

@Component({
  selector: "src-tos",
  templateUrl: "./tos.component.html",
  viewProviders: [{provide: ControlContainer, useExisting: NgForm}]
})
export class TosComponent {
  @Input() signup: Signup;
  @Input() signupform: NgForm;

  constructor(protected appDataService: AppDataService) {
  }
}
